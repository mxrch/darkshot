from config import cfg
from main import main
import click


# Click config
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--threads', '-t',
    help='Number of threads',
    show_default=True,
    type=int,
    default=cfg["threads_num"]
)
@click.option(
    '--mode', '-m',
    help="""The mode to catch the more recent link, using it as a limit. (noisy, stealth)\n
            - noisy : it uploads a picture to get the more recent link\n
            - stealth : it uses the last link shown on Twitter here : https://prntscr.com/twitter.json\n""",
    show_default=True,
    type=str,
    default="noisy"
)
@click.option(
    '--algo', '-a',
    help='Algorithm used to generate links. (ascending, descending, random)',
    show_default=True,
    type=str,
    default="descending"
)
@click.option(
    '--debug', '-d',
    help='Verbose mode, for debugging.',
    show_default=True,
    is_flag=True
)
@click.option(
    '--resume_ro', '-ro',
    help="Don't save the resume state, only read it.",
    show_default=True,
    is_flag=True
)
@click.option(
    '--clean', '-c',
    type=str,
    help="""Clean some things you don't want anymore. (logs, resume, exports)\n
            If you want want to specify multiple values, specify them comma-separated and without spaces. Ex: \"--clean logs,exports\""""
)
def start(threads, mode, algo, debug, clean, resume_ro):
    main(threads, mode, algo, debug, clean, resume_ro)

if __name__ == '__main__':
	start()