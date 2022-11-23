import argparse
import functools
import http.server
import shutil
import socketserver
import sys
from pathlib import Path

from pyblog.blog import Blog
from pyblog.post import Post

DEFAULT_TEST_PORT = 9090
DEFAULT_TEST_HOST = 'localhost'


def parse_cli_arguments():
    parser = argparse.ArgumentParser(prog='pyblog', description='A static blog site generator')

    subparsers = parser.add_subparsers(title='subcommands', dest='command', description='valid subcommands', required=True)

    parser_init = subparsers.add_parser('init', help='Creates a new pyblog website')
    parser_init.add_argument('path', help='Initializes all the relevant files for the website on the input path')

    parser_build = subparsers.add_parser('build', help='Builds the website')
    parser_build.add_argument('--force', help='Force a clean rebuild of the entire website', action='store_true')

    subparsers.add_parser('test', help='Creates a local server to check the blog locally')

    return parser.parse_args()


def init(path: Path):
    pyblog = Blog(path.expanduser())
    pyblog.create()
    print(f'New Pyblog successfully created on {path.absolute()}!')


def build(blog: Blog, force: bool):
    blog.load_config()
    shutil.copytree(blog.style_sheets_path, blog.website_path, dirs_exist_ok=True)
    all_public_posts = []
    needs_rebuild = False

    if blog.config_path.stat().st_mtime > blog.last_modified_file_path.stat().st_mtime:
        print(f'The config.json file has been modified. Rebuilding the whole site.')
        needs_rebuild = True
        blog.last_modified_file_path.touch(exist_ok=True)

    for path in blog.markdown_post_paths():
        target_path = blog.get_post_target_html_path(path)
        post = Post(path, target_path)
        all_public_posts.append(post)
        if post.is_public() and (post.is_dirty(target_path) or force or needs_rebuild):
            print(f'Building post {post.source_path}...')
            blog.build_post(post)
            if not needs_rebuild:
                needs_rebuild = True

    # Cleanup: If a post was deleted after it had been published, then we need to delete the corresponding html file.
    for target_path in blog.orphan_target_paths():
        print(f'Deleting orphan page: {target_path}')
        target_path.unlink()

    if not needs_rebuild:
        print('No new posts found!')
    else:
        all_public_posts.sort(key=lambda x: x.date, reverse=True)
        latest_posts = all_public_posts[:blog.HOME_MAX_POSTS]  # Maybe handle this within the blog instance
        print(f'Building index...')
        blog.build_home_page(latest_posts)
        print(f'Building tag pages...')
        blog.build_tag_pages(all_public_posts)
        print(f'Done!')


def serve(blog: Blog):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=blog.website_path)
    with socketserver.TCPServer((DEFAULT_TEST_HOST, DEFAULT_TEST_PORT), handler) as httpd:
        print(f'Test server running on: http://{DEFAULT_TEST_HOST}:{DEFAULT_TEST_PORT}')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()


def execute():
    args = parse_cli_arguments()

    if args.command == 'init':
        init(Path(args.path))

    else:
        pyblog = Blog(Path('.'))
        if not pyblog.is_pyblog():
            print('Error: The current path does not contain a pyblog')
            return 1

        if args.command == 'build':
            build(pyblog, args.force)

        elif args.command == 'test':
            serve(pyblog)

        elif args.command == 'rollback_config':
            rollback_config(pyblog)


if __name__ == '__main__':
    sys.exit(execute())
