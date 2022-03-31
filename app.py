import os
from flask import Flask, request
from github import Github, GithubIntegration

app = Flask(__name__)
#  executar o smee
# smee -u https://smee.io/ZYAcdwxT4eHfU27P --port 5000
app_id = 184664 #'<your_app_number_here>'

# Read the bot certificate
with open(
        os.path.normpath(os.path.expanduser('bot_key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()
    
# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)


def pr_opened_event(repo, payload):
    pr = repo.get_issue(number=payload['pull_request']['number'])
    author = pr.user.login
    #f"Thanks for opening this pull request, @{author}! " \
    is_first_pr = repo.get_issues(creator=author).totalCount
    if is_first_pr == 1: 
        response = f"Thanks for opening this pull request, ! " \
                   f"The repository maintainers will look into it ASAP! :speech_balloon:"
        pr.create_comment(f"{response}")
        pr.add_to_labels("needs review")
    

def pr_closed_event(repo, payload):
    pr = repo.get_pull(number=payload['pull_request']['number'])
    author = pr.user.login
    if pr.merged:
        prIssue = repo.get_issue(number=payload['pull_request']['number'])
        
        response = f"Thank you @{author} for pull request merged! "                  
        prIssue.create_comment(f"{response}")   
        
        ref = pr.head.ref
        #branch = repo.get_branch(ref)
        branch = repo.get_git_ref(f"heads/{ref}")
        branch.delete()
        #repo.get_branch('feature-branch-1').delete()
        #branches = repo.get_branches()
        #print(list(branches))
        #print("branch ",branch.name)
        #print("branch commit ",branch.commit)
        #print("branch protected ",branch.protected)
   
@app.route("/", methods=['POST'])
def bot():
    
    payload = request.json

    if not 'repository' in payload.keys():
        return "", 204

    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']

    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")
    #print(list(repo.get_branches()))
    
    
    # Check if the event is a GitHub pull request creation event
    if all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'opened':      
        pr_opened_event(repo, payload)

    # Check if the event is a GitHub pull request creation event and the action is "closed"
    elif all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'closed': 
        pr_closed_event(repo, payload)

    return "", 204

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
