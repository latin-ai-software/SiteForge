# GitLab CI/CD Setup Guide

## Current Status: CI is Working! ✅

Your GitLab CI pipeline is now successfully cloning the repository and submodules. The SSH key setup is optional and the pipeline will continue even if SSH keys are not configured.

## SSH Key Configuration (Optional)

Since GitLab CI is automatically handling repository authentication, SSH keys are only needed if you want to:
- Push commits from CI jobs
- Access additional private repositories
- Use SSH for other Git operations

### 1. Generate SSH Key Pair (Optional)

```bash
# Generate a new SSH key pair (don't use a passphrase)
ssh-keygen -t rsa -b 4096 -C "ci@gitlab.local" -f ~/.ssh/gitlab_ci_key
```

### 2. Add Public Key to GitLab Deploy Keys (Optional)

1. Go to your GitLab project: `https://git.latinai.de/your-project/-/settings/repository`
2. Expand "Deploy keys"
3. Click "Add new key"
4. Title: `CI Deploy Key`
5. Key: Paste the contents of `~/.ssh/gitlab_ci_key.pub`
6. Check "Grant write permissions to this key" (if needed)
7. Click "Add key"

### 3. Add Private Key to GitLab CI Variables (Optional)

1. Go to your GitLab project: `https://git.latinai.de/your-project/-/settings/ci_cd`
2. Expand "Variables"
3. Click "Add variable"
4. Key: `SSH_PRIVATE_KEY`
5. Value: Paste the entire contents of `~/.ssh/gitlab_ci_key` (private key)
6. Type: `Variable` (not protected or masked)
7. Click "Add variable"

### Alternative: Use Personal Access Token

If you prefer HTTPS authentication:

1. Create a Personal Access Token in GitLab:
   - Go to `https://git.latinai.de/-/profile/personal_access_tokens`
   - Name: `CI Token`
   - Scopes: `read_repository`, `write_repository` (if needed)
   - Create token

2. Add to CI variables:
   - Key: `GITLAB_TOKEN`
   - Value: Your personal access token

## Current CI Status

- ✅ Repository cloning: Working (GitLab CI handles authentication automatically)
- ✅ Submodule cloning: Working (inherits parent repository credentials)
- ✅ Test execution: Should work now
- ✅ Coverage reporting: Fixed to generate XML format
- ✅ Security scanning: Ready to run

## Troubleshooting

- **"SSH key setup failed"**: This is normal if SSH_PRIVATE_KEY is not set - the pipeline continues
- **"No files to upload"**: Tests didn't run - check the job logs for errors
- **Permission denied**: Check deploy key permissions or use personal access token

## Security Notes

- SSH keys are more secure than personal access tokens
- Rotate keys regularly
- Use separate keys for different projects
- Never commit private keys to the repository