import argparse
import datetime
import pathlib

import git
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Git リポジトリの貢献度（挿入・削除行数、コミット数）を著者ごとに集計してグラフ化します。",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="対象の Git リポジトリのパス（デフォルト: カレントディレクトリ）",
    )

    date_group = parser.add_argument_group("日付範囲指定")
    date_group.add_argument(
        "--since-date",
        help="開始日 (YYYY-MM-DD)。指定した日付を含みます。",
    )
    date_group.add_argument(
        "--until-date",
        help="終了日 (YYYY-MM-DD)。指定した日付を含みます。",
    )

    commit_group = parser.add_argument_group("コミット範囲指定")
    commit_group.add_argument(
        "--since-commit",
        help="開始コミット ID（このコミットの次から集計したい場合は '<id>^' のように指定）",
    )
    commit_group.add_argument(
        "--until-commit",
        help="終了コミット ID（省略時は HEAD とみなします）",
    )

    args = parser.parse_args()

    if (args.since_commit or args.until_commit) and (
        args.since_date or args.until_date
    ):
        parser.error("日付による範囲指定とコミット ID による範囲指定は同時に使えません。")

    return args


def parse_date(date_str: str | None) -> datetime.datetime | None:
    if not date_str:
        return None
    return datetime.datetime.strptime(date_str, "%Y-%m-%d")


def build_range_spec(
    repo: git.Repo, args: argparse.Namespace
) -> tuple[datetime.datetime | None, datetime.datetime | None, str | None]:
    since_date = parse_date(args.since_date)
    until_date = parse_date(args.until_date)

    rev_spec: str | None = None
    if args.since_commit or args.until_commit:
        since_commit = args.since_commit
        until_commit = args.until_commit or "HEAD"
        if since_commit:
            rev_spec = f"{since_commit}..{until_commit}"
        else:
            rev_spec = until_commit
        # コミット ID 指定モードでは日付による絞り込みはしない
        since_date = None
        until_date = None

    return since_date, until_date, rev_spec


def collect_author_stats(
    repo: git.Repo,
    since_date: datetime.datetime | None = None,
    until_date: datetime.datetime | None = None,
    rev_spec: str | None = None,
) -> tuple[dict[str, dict[str, int]], datetime.datetime, datetime.datetime]:
    author_stats: dict[str, dict[str, int]] = {}
    latest_date: datetime.datetime | None = None
    earliest_date: datetime.datetime | None = None

    commits = repo.iter_commits(rev_spec) if rev_spec else repo.iter_commits()

    for item in commits:
        commit_date = datetime.datetime.fromtimestamp(item.committed_date)

        # 日付範囲指定がある場合のみフィルタ
        if until_date and commit_date > until_date:
            continue
        if since_date and commit_date < since_date:
            # iter_commits は新しい順なので、ここで break してよい
            break

        if len(item.parents) > 1:
            # マージコミット除外
            continue

        if latest_date is None or commit_date > latest_date:
            latest_date = commit_date
        if earliest_date is None or commit_date < earliest_date:
            earliest_date = commit_date

        author_name = item.author.name
        if author_name not in author_stats:
            author_stats[author_name] = {
                "insertions": 0,
                "deletions": 0,
                "commits": 0,
            }

        file_stats = item.stats.files
        for stats in file_stats.values():
            author_stats[author_name]["insertions"] += stats.get("insertions", 0)
            author_stats[author_name]["deletions"] += stats.get("deletions", 0)

        # コミット数はコミット単位で 1 カウント
        author_stats[author_name]["commits"] += 1

    if latest_date is None or earliest_date is None:
        raise ValueError("指定された範囲に該当するコミットが見つかりませんでした。")

    return author_stats, earliest_date, latest_date


def sort_author_stats(
    author_stats: dict[str, dict[str, int]]
) -> list[tuple[str, dict[str, int]]]:
    return sorted(
        author_stats.items(),
        key=lambda x: (x[1]["insertions"] + x[1]["deletions"]),
    )


def print_author_stats(sorted_data: list[tuple[str, dict[str, int]]]) -> None:
    for author, stats in sorted_data:
        print(
            f"{author}: "
            f"+{stats['insertions']} "
            f"-{stats['deletions']} "
            f"commits={stats['commits']}"
        )


def plot_author_stats(
    repo: git.Repo,
    sorted_data: list[tuple[str, dict[str, int]]],
    earliest_date: datetime.datetime,
    latest_date: datetime.datetime,
) -> str:
    repo_path_obj = pathlib.Path(repo.working_tree_dir or ".")

    left = np.arange(len(sorted_data))
    labels = [name for name, _ in sorted_data]
    ins_height = [stats["insertions"] for _, stats in sorted_data]
    del_height = [stats["deletions"] for _, stats in sorted_data]
    commit_counts = [stats["commits"] for _, stats in sorted_data]

    bar_width = 0.3
    fig, ax1 = plt.subplots()
    ax1.bar(left, ins_height, color="r", width=bar_width, align="center", label="insertions")
    ax1.bar(
        left + bar_width,
        del_height,
        color="b",
        width=bar_width,
        align="center",
        label="deletions",
    )
    ax1.set_ylabel("lines changed")

    # コミット数は第 2 軸の折れ線グラフとして描画
    ax2 = ax1.twinx()
    ax2.plot(
        left + bar_width / 2,
        commit_counts,
        color="g",
        marker="o",
        linestyle="-",
        label="commits",
    )
    ax2.set_ylabel("commits")

    ax1.set_xticks(left + bar_width / 2)
    ax1.set_xticklabels(labels, rotation=30, fontsize="small")

    # 2 つの軸の凡例をまとめて表示
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(handles1 + handles2, labels1 + labels2, loc="upper right", bbox_to_anchor=(1, 1))

    fig.tight_layout()

    date_range_str = (
        f"({earliest_date.strftime('%Y%m%d')}-" f"{latest_date.strftime('%Y%m%d')})"
    )
    branch_name = getattr(repo.active_branch, "name", "DETACHED_HEAD")
    png_file_name = (
        repo_path_obj.name + "_" + branch_name + "_" + date_range_str + ".png"
    )
    fig.savefig(png_file_name)
    return png_file_name


def main() -> None:
    args = parse_args()
    repo = git.Repo(args.repo)

    since_date, until_date, rev_spec = build_range_spec(repo, args)
    author_stats, earliest_date, latest_date = collect_author_stats(
        repo, since_date=since_date, until_date=until_date, rev_spec=rev_spec
    )

    sorted_data = sort_author_stats(author_stats)
    print_author_stats(sorted_data)

    output_path = plot_author_stats(
        repo, sorted_data, earliest_date=earliest_date, latest_date=latest_date
    )
    print("output:" + output_path)


if __name__ == "__main__":
    main()
