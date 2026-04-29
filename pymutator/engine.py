import libcst as cst
import random
from typing import List
from rich.progress import Progress, BarColumn, TaskProgressColumn
from libcst.metadata import MetadataWrapper
from .mutators import Visitor, Transformer
from .runner import run_tests, Status
from .models import MutationResult, Config

def start_mutators_process(source_code: str, config: Config) -> List[MutationResult]:
    """
    Generate mutants from source code, execute tests for each, and collect results.

    Args:
        source_code (str): The original Python source code.
        config (Config): Project configuration including mutant count and paths.

    Returns:
        List[MutationResult]: A list of objects containing the result for each mutant.
    """

    tree = cst.parse_module(source_code)

    visitor = Visitor()
    MetadataWrapper(tree).visit(visitor)
    max_mutant_cnt = visitor.counter
    lines_mutations = visitor.all_mutations
    results = []

    mutant_cnt = min(config.mutant_cnt, max_mutant_cnt)
    if mutant_cnt == 0:
        return []

    targets = random.sample(range(1, max_mutant_cnt + 1), mutant_cnt)
    targets.sort()

    with Progress(BarColumn(), TaskProgressColumn()) as progress:
        task_id = progress.add_task("Testing...", total=len(targets))

        for target in targets:
            transformer = Transformer(target)
            mutant_tree = tree.visit(transformer)
            status = run_tests(mutant_tree.code, config)
            results.append(MutationResult(target, lines_mutations[target], status))
            progress.advance(task_id)

    return results
