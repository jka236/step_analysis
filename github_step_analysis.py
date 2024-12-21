from github import Github
from github.PullRequest import PullRequest
from github import File
from typing import List, Dict
import base64
import os
from step_analysis import StepDefinitionAnalyzer
from dotenv import load_dotenv
import json

class GithubStepAnalyzer:
    def __init__(self, github_token: str, repo_name: str, model: str = "gpt-4o-mini"):
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repo_name)
        self.analyzer = StepDefinitionAnalyzer(model=model)
        
    def analyze_pull_request(self, pr_number: int) -> Dict:
        """
        Analyze only the changed step definitions in a pull request and post results as comments
        """
        pr = self.repo.get_pull(pr_number)
        results = []
        
        # Get modified files
        files = pr.get_files()
        commit = pr.get_commits()
        for file in files:
            if self._is_step_definition(file.filename):
                # Get the patch/diff content
                patch = file.patch
                if not patch:
                    continue
                    
                # Extract only the added/modified lines
                changed_content = self._extract_changed_content(patch)
                if not changed_content:
                    continue
                
                # Analyze only the changed step definitions
                analysis = self.analyzer.analyze_step(
                    target_step=str(changed_content),
                    project_root=self._get_project_files(pr)
                )
                # analysis = "test"
                results.append({
                    "file": file.filename,
                    "analysis": analysis,
                    "changes": changed_content
                })
                
                # Post comment with analysis
                self._post_analysis_comment(pr, file, analysis, changed_content)
        
        return results
    
    def _extract_changed_content(self, patch: str) -> List[Dict[str, any]]:
        """
        Extract added or modified lines from the patch along with their line numbers
        
        Returns:
            List of dictionaries containing line content and number
            [{'content': 'line content', 'line_number': int}, ...]
        """
        if not patch:
            return []
            
        changed_lines = []
        current_line = 0
        
        for line in patch.split('\n'):
            if line.startswith('@@'):
                # Parse the line number from the @@ -l,s +l,s @@ line
                # Format is usually "@@ -l,s +l,s @@" where l is the starting line and s is the size
                try:
                    line_info = line.split('+')[1].split(',')[0]
                    current_line = int(line_info) - 1  # -1 because we increment before using
                except (IndexError, ValueError):
                    continue
            else:
                current_line += 1
                # Only include added or modified lines (starting with '+')
                # Exclude the diff metadata lines (starting with '+++')
                if line.startswith('+') and not line.startswith('+++'):
                    changed_lines.append({
                        'content': line[1:],  # Remove the '+' prefix
                        'line_number': current_line
                    })
        
        return changed_lines

    
    def _is_step_definition(self, filename: str) -> bool:
        """Check if file is a step definition file"""
        return (
            filename.endswith("Steps.java") or
            filename.endswith("StepDefinitions.java") or
            filename.endswith("StepsImpl.java") or
            filename.endswith("StepDefs.java")
        )
        
    def _get_file_content(self, raw_url: str) -> str:
        """Get content of a file from GitHub"""
        file = self.github.get_repo(self.repo.full_name).get_contents(raw_url)
        return base64.b64decode(file.content).decode('utf-8')
    
    def _get_project_files(self, pr: PullRequest) -> str:
        """
        Create a temporary directory with project files for context
        """
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        
        # Get repository files
        contents = self.repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            else:
                try:
                    # Create directory structure
                    file_path = os.path.join(temp_dir, file_content.path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Download file
                    with open(file_path, 'wb') as f:
                        f.write(base64.b64decode(file_content.content))
                except Exception as e:
                    print(f"Error downloading {file_content.path}: {e}")
        
        return temp_dir
    
    def _post_analysis_comment(self, pr: PullRequest, file: File, analysis: Dict, changed_content: str) -> None:
        """Post analysis results as a PR comment"""
        analysis = json.loads(analysis)
        for idx, _ in enumerate(analysis["issues"]):
            # Format comment
            comment = f"""
### Issues Found:
{analysis['issues'][idx]}

### Suggestions:
{analysis['suggestions'][idx]}
"""

            # Get the latest commit in the PR
            commit = list(pr.get_commits())[-1]
            
            # Create comment on the specific file
            pr.create_review_comment(
                body=comment,
                commit=commit,
                path=file.filename,
                line=analysis['line_number'][idx]
            )
        
    @staticmethod
    def _format_list(items: List[str]) -> str:
        """Format a list into markdown bullet points"""
        return "\n".join(f"- {item}" for item in items)

# Example usage in GitHub Actions
if __name__ == "__main__":
    load_dotenv()
    
    # Get environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER"))
    
    # Initialize and run analyzer
    analyzer = GithubStepAnalyzer(github_token, repo_name)
    results = analyzer.analyze_pull_request(pr_number)
    print(results)