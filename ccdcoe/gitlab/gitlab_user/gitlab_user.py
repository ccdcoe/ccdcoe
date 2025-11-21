from gitlab.v4.objects import CurrentUser, User

from ccdcoe.gitlab.gitlab_base import GitlabBase


class GitlabUser(GitlabBase):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f"<<{__class__.__name__}>>"

    def get_current_gitlab_user(self) -> CurrentUser:
        with self.get_gitlab_obj() as gl:
            gl.auth()
            current_user = gl.user
            return current_user

    def get_gitlab_user(self, user_id: int) -> User:
        with self.get_gitlab_obj() as gl:
            gl.auth()
            user = gl.users.get(user_id)
            return user
