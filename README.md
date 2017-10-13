# UWSEDS Course Managment

## Test Users

It's **highly** encouraged to run an integration test of any
manipulation of live student repositories. UWSEDS has 5 non-admin test users
under the github usernames `uwseds-test[n]` with the password `test5uwseds`.

In general, run a test of any functionality by establishing a dummy assignment,
setup the test users as students and then execute the managment script.

## Peer Review
`peer_review` contains a script to establish issue-based peer reviews for a
student assignment. In short, the script lists all repositories for a specific
classroom assignment, uses this to generate a student list, and then assigns
random reviewers to each student repo. Reviewers are added as collaborators to
their reviewee's repo and a per-reviewer issue is opened using a review
template.

See `example_config.json` for details.
