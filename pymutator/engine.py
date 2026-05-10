import multiprocessing as mp
import libcst as cst
import difflib
import random
from typing import List
from rich.progress import Progress, BarColumn, TaskProgressColumn
from libcst.metadata import MetadataWrapper
from .mutators import Visitor, Transformer
from .runner import run_tests
from .models import MutationResult, Config

def worker(args) -> MutationResult:
    """ Worker for multiprocessing """
    source_code, config, target, line_num = args

    tree = cst.parse_module(source_code)
    transformer = Transformer(target, config.enabled_mutations)
    mutant_tree = tree.visit(transformer)

    status = run_tests(mutant_tree.code, config)

    diff_list = list(difflib.unified_diff(
        source_code.splitlines(),
        mutant_tree.code.splitlines(),
        fromfile="original",
        tofile=f"mutant_{target}",
        n=0
    ))

    diff = "\n".join(diff_list)

    return MutationResult(target, line_num, status, diff)


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

    visitor = Visitor(config.enabled_mutations)
    MetadataWrapper(tree).visit(visitor)
    max_mutant_cnt = visitor.counter
    lines_mutations = visitor.all_mutations
    results = []

    mutant_cnt = min(config.mutant_cnt, max_mutant_cnt)
    if mutant_cnt == 0:
        return []

    targets = random.sample(range(1, max_mutant_cnt + 1), mutant_cnt)
    targets.sort()

    if config.jobs <= 1:
        with Progress(BarColumn(), TaskProgressColumn()) as progress:
            task_id = progress.add_task("Testing...", total=len(targets))

            for target in targets:
                results.append(worker((source_code, config, target, lines_mutations[target])))
                progress.advance(task_id)

    else:
        worker_args = [(source_code, config, target, lines_mutations[target]) for target in targets]

        with Progress(BarColumn(), TaskProgressColumn()) as progress:
            task_id = progress.add_task("Testing multiprocessing...", total=len(targets))

            with mp.Pool(processes=config.jobs) as pool:
                for res in pool.imap_unordered(worker, worker_args):
                    results.append(res)
                    progress.advance(task_id)

    return results
