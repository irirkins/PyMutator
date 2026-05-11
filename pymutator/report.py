from rich.panel import Panel
from rich.console import Console
from rich.syntax import Syntax
from .runner import Status

def report(results, config):
    total = len(results)
    console = Console()

    if total == 0:
        console.print("No mutants were generated")

    survived = sum(1 for res in results if res.status == Status.SURVIVED)
    killed = sum(1 for res in results if res.status == Status.KILLED)
    timeouts = sum(1 for res in results if res.status == Status.TIMEOUT)

    survival_rate = (survived / total) * 100
    mutation_score = (killed / total) * 100

    summary_text = (
        f"Total mutants count: [bold]{total}[/bold]\n"
        f"Survived: [bold red]{survived}[/bold red]\n"
        f"Killed: [bold green]{killed}[/bold green]\n"
        f"Timeout: [bold yellow]{timeouts}[/bold yellow]\n"
        f"---------------------------\n"
        f"Survival rate: [bold red]{survival_rate:.2f}%[/bold red]\n"
        f"Mutation Score: [bold green]{mutation_score:.2f}%[/bold green]"
    )

    console.print(Panel(summary_text, title="[bold blue]Final Statistic[/bold blue]", expand=False))

    if config.full_report:
        console.print("\n[bold red]Survived mutants:[/bold red]")
        for res in results:
            if res.status == Status.SURVIVED:
                console.print(f"\n[bold]Mutant #{res.number} (Kine {res.line})[/bold]")
                syntax = Syntax(res.diff, "diff", theme="monokai", line_numbers=False)
                console.print(syntax)
