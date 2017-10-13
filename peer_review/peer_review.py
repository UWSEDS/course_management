import getpass
import pprint
import random
import collections
import os

import traitlets
from traitlets import Bool, Integer, Unicode, HasTraits, default, Set, Dict
from traitlets.config import Application

import github3

class ReviewManager(Application):
    username = Unicode(
        help="Admin user github username. Must be organization owner.").tag(config=True)
    
    @default('username')
    def _default_username(self):
        return getpass.getuser()
    
    password = Unicode()
    
    org = Unicode(allow_none=False,
        help="Classroom organization.").tag(config=True)
    repo_prefix = Unicode("",
        help="Assignment repository prefix, eg. 'hw-1-'. Repository title after prefix is target username.").tag(config=True)
    skip_users = Set(trait=Unicode(allow_none=False),
        help="Skip given user's repos when establishing reviews, used to skip instructor/example repos.").tag(config=True)
    
    num_reviewers = Integer(2,
        help="Number of reviewers added per project").tag(config=True)
    review_title_template = Unicode("Peer Review: %s",
        help="Issue title format, % formatted with reviewer username.").tag(config=True)
    
    review_template_file = Unicode(
        help="File containing a markdown review template for peer review issues.").tag(config=True)
    review_template = Unicode(
        help="Markdown review template for peer review issues.").tag(config=True)
    
    dry_run = Bool(True,
        help="Load classroom data and log events, but do not perform github updates.").tag(config=True)
    
    def setup_reviews(self):
        gh = github3.login(
            username=self.username,
            password=self.password if self.password else getpass.getpass("%s github password: " % self.username))
        self.log.info("Got github: %s", gh)
        
        org = gh.organization(self.org)
        self.log.info("Got organization: %s", org)
        
        repos = [r for r in org.repositories() if r.name.startswith(self.repo_prefix)]
        self.log.info("Got repo count: %i", len(repos))
        
        repos_by_user = { r.name[len(self.repo_prefix):] : r for r in repos}
        self.log.info("Repo list:\n%s", pprint.pformat(repos_by_user))
        for n in self.skip_users:
            if n in repos_by_user:
                self.log.info("Skipping user repo: %s", n)
                del repos_by_user[n]
        
        user_list = list(repos_by_user)
        random.shuffle(user_list)
        
        reviewers = {
            user_list[n] : [
                user_list[(n+1+i) % len(user_list)] for i in range(self.num_reviewers)
            ]
            for n in range(len(user_list))
        }
        
        self.log.info("Reviewers:\n%s", pprint.pformat(reviewers))
        
        # Run a self-test of the reviewer list
        review_counts = collections.Counter()
        for n, r in reviewers.items():
            assert(len(r) == self.num_reviewers)
            assert(len(set(r)) == len(r))
            assert n not in r
            review_counts.update(r)
            
        assert(len(review_counts) == len(user_list))
        assert(set(review_counts) == set(user_list))
        for u in user_list:
            assert review_counts[u] == self.num_reviewers
            
        assert self.review_template_file or self.review_template
        
        if self.review_template_file:
            review_template = open(self.review_template_file, "r").read()
        elif self.review_template:
            review_template = self.review_template
        
        self.log.info("Review template:\n%s", review_template)
        for u in user_list:
            urepo = repos_by_user[u]
            for r in reviewers[u]:
                self.log.info("Add collaborator %s: %s", urepo, r)
                if not self.dry_run:
                    urepo.add_collaborator(r)
                    
                self.log.info("Create review issue %s: %r", urepo, self.review_title_template % r)
                if not self.dry_run:
                    urepo.create_issue(
                        title="Peer Review: %s" % r,
                        body=self.review_template,
                        labels=["peer_review"],
                        assignee=r
                    )
                    
    config_file = Unicode(u'', help="Load this config file").tag(config=True)

    aliases = {"config_file" : "ReviewManager.config_file"}
    flags = Dict(dict(
        no_dry_run=({'ReviewManager': {'dry_run' : False}}, "Enable github api calls.")
    ))
    
    def initialize(self, argv=None):
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)

def main():
    app = ReviewManager()
    app.initialize()
    app.setup_reviews()

if __name__ == "__main__":
    ReviewManager.log_level.default_value = 'INFO'
    main()
