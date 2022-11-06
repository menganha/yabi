import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from pyblog.post import Post


class Blog:
    TEMPLATE_DIR_NAME = 'templates'
    WEBSITE_DIR_NAME = 'public'
    POSTS_DIR_NAME = 'posts'
    TAGS_DIR_NAME = 'tags'
    HOME_MAX_POSTS = 10
    POST_TEMPLATE = 'post.html'
    TAG_TEMPLATE = 'tag.html'
    ALL_TAGS_TEMPLATE = 'all_tags.html'
    INDEX_TEMPLATE = 'index.html'
    CONFIG_FILE_NAME = 'config.json'

    def __init__(self, main_path: Path):
        self.main_path = main_path
        self.website_path = main_path / self.WEBSITE_DIR_NAME
        self.website_posts_path = self.website_path / self.POSTS_DIR_NAME
        self.website_tags_path = self.website_path / self.TAGS_DIR_NAME
        self.posts_path = main_path / self.POSTS_DIR_NAME
        self.template_path = main_path / self.TEMPLATE_DIR_NAME
        self.template_environment = Environment(loader=FileSystemLoader(self.template_path), trim_blocks=True)
        self.config = main_path / 'config.json'

        # self.template_environment.globals.update({'website_name': self.name})
        # self.name = main_path.resolve().name
        # self.template_environment.globals['website_name'] = self.name

    def create(self):
        if self.is_pyblog():
            print(f'Error: Input path {self.main_path} seems to contain another pyblog')
            return 1
        elif not self.is_pyblog() and self.main_path.exists():
            print(f'Error: Input path {self.main_path} already exists. Please choose a another path to create a pyblog')
            return

        local_template_path = Path(__file__).parent.parent / self.TEMPLATE_DIR_NAME

        self.main_path.mkdir(parents=True)
        self.website_path.mkdir()
        self.posts_path.mkdir()
        self.website_posts_path.mkdir()
        self.website_tags_path.mkdir()
        shutil.copytree(local_template_path, self.template_path)
        print(f'New pyblog created successfully on {self.main_path}!')

    def is_pyblog(self) -> bool:
        """ Checks whether the current directory is a pyblog, i.e., it has the relevant paths"""
        if self.website_path.exists() and self.posts_path.exists() and self.template_path.exists():
            return True
        else:
            return False

    def build_home_page(self, posts: list[Post]):
        index_template = self.template_environment.get_template(self.INDEX_TEMPLATE)
        index_html = index_template.render(latest_posts=posts)
        target_path = self.website_path / 'index.html'
        target_path.write_text(index_html)

    def build_tag_pages(self, all_posts: list[Post]):
        all_tags = set([tag for post in all_posts for tag in post.tags])
        grouped_posts = [(tag, [post for post in all_posts if tag in post.tags]) for tag in all_tags]

        tag_template = self.template_environment.get_template(self.TAG_TEMPLATE)
        for tag, group in grouped_posts:
            tag_html = tag_template.render(tag=tag, latest_posts=group[:self.HOME_MAX_POSTS])
            target_path = self.website_tags_path / f'{tag}.html'
            target_path.write_text(tag_html)

        all_tags_template = self.template_environment.get_template(self.ALL_TAGS_TEMPLATE)
        all_tags_html = all_tags_template.render(all_tags=all_tags)
        target_path = self.website_path / f'tags.html'
        target_path.write_text(all_tags_html)

    def _get_post_target_html_path(self, post_path: Path) -> Path:
        return self.website_posts_path / post_path.parent.relative_to(self.posts_path) / f'{post_path.stem}.html'

    def get_all_public_posts(self) -> list[Post]:
        """ Retrieves and enriches all posts and sorts them by date """
        all_public_posts = []
        for post_path in self.posts_path.rglob('*md'):
            target_path = self._get_post_target_html_path(post_path)
            post = Post(post_path, target_path, self.website_path)
            if post.is_public():
                all_public_posts.append(post)
        all_public_posts.sort(key=lambda x: x.date, reverse=True)
        return all_public_posts

    def build_post(self, post: Post):
        post_template = self.template_environment.get_template(self.POST_TEMPLATE)
        html_content = post.get_markdown_html()
        post_html = post_template.render(post=post, content=html_content)
        post._html_target_path.write_text(post_html)  # TODO: Change it to something more beautiful!