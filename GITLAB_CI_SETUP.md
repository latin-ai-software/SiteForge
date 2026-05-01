# GitLab CI/CD Setup Guide

## SSH Key Configuration for Private Repository Access

Since your repository is hosted on a private GitLab instance (`git.latinai.de`), the CI pipeline needs authentication to clone the repository. Here's how to set it up:

### 1. Generate SSH Key Pair

```bash
# Generate a new SSH key pair (don't use a passphrase)
ssh-keygen -t rsa -b 4096 -C "ci@gitlab.local" -f ~/.ssh/gitlab_ci_key
```

### 2. Add Public Key to GitLab Deploy Keys

1. Go to your GitLab project: `https://git.latinai.de/your-project/-/settings/repository`
2. Expand "Deploy keys"
3. Click "Add new key"
4. Title: `CI Deploy Key`
5. Key: Paste the contents of `~/.ssh/gitlab_ci_key.pub`
6. Check "Grant write permissions to this key" (if needed)
7. Click "Add key"

### 3. Add Private Key to GitLab CI Variables

1. Go to your GitLab project: `https://git.latinai.de/your-project/-/settings/ci_cd`
2. Expand "Variables"
3. Click "Add variable"
4. Key: `SSH_PRIVATE_KEY`
5. Value: Paste the entire contents of `~/.ssh/gitlab_ci_key` (private key)
6. Type: `Variable` (not protected or masked)
7. Click "Add variable"

### 4. Alternative: Use Personal Access Token

If you prefer HTTPS authentication:

1. Create a Personal Access Token in GitLab:
   - Go to `https://git.latinai.de/-/profile/personal_access_tokens`
   - Name: `CI Token`
   - Scopes: `read_repository`, `write_repository` (if needed)
   - Create token

2. Add to CI variables:
   - Key: `GITLAB_TOKEN`
   - Value: Your personal access token

3. Update `.gitlab-ci.yml` to use HTTPS instead of SSH (modify the before_script sections)

### 5. Verify Setup

After configuring SSH keys, push a new commit to trigger the CI pipeline. The jobs should now be able to clone the repository successfully.

## Troubleshooting

- **"Host key verification failed"**: The SSH host key for `git.latinai.de` wasn't added to known_hosts
- **"Permission denied"**: The deploy key doesn't have read access or the private key is incorrect
- **"Could not resolve hostname"**: Check that `git.latinai.de` is accessible from your runner

## Security Notes

- SSH keys are more secure than personal access tokens
- Rotate keys regularly
- Use separate keys for different projects
- Never commit private keys to the repository