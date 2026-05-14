"""Headless mastering CLI."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .process import process_song
from .presets.base import PresetStyle

console = Console()

STYLE_CHOICES = [s.value for s in PresetStyle]


def _parse_overrides(overrides: tuple[str, ...]) -> dict:
    """Parse KEY=VALUE pairs into a dict."""
    result = {}
    for item in overrides:
        if "=" not in item:
            raise click.BadParameter(f"Override must be KEY=VALUE, got: {item}")
        key, val = item.split("=", 1)
        try:
            result[key] = float(val)
        except ValueError:
            result[key] = val
    return result


@click.group()
@click.version_option()
def cli():
    """Rubin headless mastering system.

    \b
    Processes raw vocal + acoustic guitar stems through professional
    mastering chains to produce three style variants:
      • analog_console  — SSL/Neve-inspired warmth and clarity
      • tape            — analog tape machine character
      • lofi            — degraded cassette/vinyl aesthetic
    """


@cli.command()
@click.argument("vocal", type=click.Path(exists=True, path_type=Path))
@click.argument("guitar", type=click.Path(exists=True, path_type=Path))
@click.argument("output_dir", type=click.Path(path_type=Path))
@click.option(
    "--style", "-s",
    multiple=True,
    type=click.Choice(STYLE_CHOICES),
    default=STYLE_CHOICES,
    show_default=True,
    help="Mastering style(s) to produce. Can be repeated.",
)
@click.option(
    "--vocal-param", "-V",
    multiple=True,
    metavar="KEY=VALUE",
    help="Override vocal chain parameter (e.g. comp_ratio=4.0). Repeatable.",
)
@click.option(
    "--guitar-param", "-G",
    multiple=True,
    metavar="KEY=VALUE",
    help="Override guitar chain parameter. Repeatable.",
)
@click.option(
    "--master-param", "-M",
    multiple=True,
    metavar="KEY=VALUE",
    help="Override master chain parameter (e.g. target_lufs=-16.0). Repeatable.",
)
@click.option("--json-output", is_flag=True, help="Output results as JSON.")
def master(vocal, guitar, output_dir, style, vocal_param, guitar_param, master_param, json_output):
    """Master VOCAL and GUITAR stems to OUTPUT_DIR.

    \b
    Produces per-style subdirectories:
      OUTPUT_DIR/stems/STYLE/     — processed stems (32-bit WAV)
      OUTPUT_DIR/mixes/           — pre-master mixes (32-bit WAV)
      OUTPUT_DIR/masters/         — final masters (.wav, .mp3, .m4a, .flac)
    """
    styles = [PresetStyle(s) for s in (style or STYLE_CHOICES)]
    vocal_overrides = _parse_overrides(vocal_param)
    guitar_overrides = _parse_overrides(guitar_param)
    master_overrides = _parse_overrides(master_param)

    if not json_output:
        console.print(Panel.fit(
            f"[bold cyan]Rubin Mastering System[/bold cyan]\n"
            f"Vocal:  {vocal.name}\n"
            f"Guitar: {guitar.name}\n"
            f"Output: {output_dir}\n"
            f"Styles: {', '.join(s.value for s in styles)}",
            border_style="cyan"
        ))

    with console.status("[bold green]Processing...[/bold green]", spinner="dots"):
        results = process_song(
            vocal_path=vocal,
            guitar_path=guitar,
            song_dir=output_dir,
            styles=styles,
            vocal_preset_overrides=vocal_overrides or None,
            guitar_preset_overrides=guitar_overrides or None,
            master_preset_overrides=master_overrides or None,
        )

    if json_output:
        serializable = {}
        for style_name, data in results.items():
            serializable[style_name] = {
                "stats": data["stats"],
                "paths": {
                    "master_wav": str(data["master_wav"]),
                    "encoded": [str(p) for p in data["encoded"]],
                    "stems": {k: str(v) for k, v in data["stems"].items()},
                    "pre_master": str(data["pre_master"]),
                },
            }
        click.echo(json.dumps(serializable, indent=2))
        return

    table = Table(title="Mastering Complete", show_header=True, header_style="bold magenta")
    table.add_column("Style", style="cyan", no_wrap=True)
    table.add_column("LUFS", justify="right")
    table.add_column("True Peak", justify="right")
    table.add_column("Files", style="green")

    for style_name, data in results.items():
        stats = data["stats"]
        lufs = f"{stats['integrated_lufs']:.1f}" if stats["integrated_lufs"] > -100 else "---"
        tp = f"{stats['true_peak_db']:.1f} dBTP"
        files = ", ".join(p.suffix for p in data["encoded"])
        table.add_row(style_name, lufs + " LUFS", tp, files)

    console.print(table)
    console.print(f"\n[bold green]✓[/bold green] Masters written to: {output_dir}")


@cli.command()
@click.option(
    "--style", "-s",
    type=click.Choice(STYLE_CHOICES),
    default="analog_console",
    show_default=True,
)
@click.option("--chain", type=click.Choice(["vocal", "guitar", "master"]), default="vocal")
def show_preset(style, chain):
    """Display all parameters for a preset."""
    from . import presets as p
    preset_map = {
        ("analog_console", "vocal"): p.ANALOG_CONSOLE_VOCAL,
        ("analog_console", "guitar"): p.ANALOG_CONSOLE_GUITAR,
        ("analog_console", "master"): p.ANALOG_CONSOLE_MASTER,
        ("tape", "vocal"): p.TAPE_VOCAL,
        ("tape", "guitar"): p.TAPE_GUITAR,
        ("tape", "master"): p.TAPE_MASTER,
        ("lofi", "vocal"): p.LOFI_VOCAL,
        ("lofi", "guitar"): p.LOFI_GUITAR,
        ("lofi", "master"): p.LOFI_MASTER,
    }
    preset = preset_map[(style, chain)]
    table = Table(title=f"{style} / {chain}", show_header=True)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", justify="right")
    for key, val in preset.model_dump().items():
        table.add_row(key, str(val))
    console.print(table)


@cli.command()
@click.argument("audio", type=click.Path(exists=True, path_type=Path))
def analyze(audio):
    """Measure LUFS and true peak of an audio file."""
    import soundfile as sf
    from .lufs import measure_lufs
    data, sr = sf.read(str(audio), dtype="float32", always_2d=True)
    stats = measure_lufs(data, sr)
    console.print(Panel.fit(
        f"[bold]{audio.name}[/bold]\n"
        f"  Integrated LUFS: [cyan]{stats['integrated_lufs']:.2f}[/cyan]\n"
        f"  True Peak:       [cyan]{stats['true_peak_db']:.2f} dBTP[/cyan]",
        border_style="blue"
    ))
