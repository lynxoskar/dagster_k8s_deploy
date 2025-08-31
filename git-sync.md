### Summary of SSH Approach for Git-Sync with Azure DevOps

The SSH method uses key-based authentication, which is more secure and doesn't expire like PATs, making it suitable for long-running GitOps flows. It involves generating SSH keys, registering the public key with Azure DevOps, and configuring git-sync to use the private key for repo access. This assumes you're using git-sync in a containerized setup (e.g., Kubernetes sidecar), but it can adapt to standalone use.

### Step-by-Step Plan

1. **Generate SSH Key Pair**:
   - On your local machine or a secure environment, run: `ssh-keygen -t ed25519 -C "your-email@example.com"`.
   - This creates a private key (`id_ed25519`) and public key (`id_ed25519.pub`) in `~/.ssh/` (or your specified path). Do not share the private key.
   - If you already have a key pair, you can reuse it, but ensure it's dedicated for this purpose.

2. **Add Public Key to Azure DevOps**:
   - Log in to your Azure DevOps organization.
   - Navigate to **User settings** (top-right profile icon) > **Security** > **SSH public keys**.
   - Click **Add**, paste the contents of your public key file (`id_ed25519.pub`), give it a name, and save.
   - Verify the key is active and has access to your internal repo (test with a local `git clone` if possible).

3. **Prepare SSH Known Hosts File**:
   - To avoid host verification errors, create a `known_hosts` file.
   - Run: `ssh-keyscan ssh.dev.azure.com >> known_hosts` (this adds the host's fingerprint).
   - Store this file securely; you'll mount it in your git-sync setup.

4. **Configure Git-Sync with SSH**:
   - Use your repo's SSH URL: `git@ssh.dev.azure.com:v3/{organization}/{project}/{repository-name}`.
   - In git-sync flags:
     - `--repo=git@ssh.dev.azure.com:v3/your-org/your-project/your-repo`
     - `--ssh-key-file=/path/to/private-key` (e.g., `/secrets/id_ed25519`)
     - `--ssh-known-hosts=true`
     - `--ssh-known-hosts-file=/path/to/known_hosts` (e.g., `/secrets/known_hosts`)
     - Add other flags like `--branch=main`, `--root=/git`, `--wait=30` for sync interval.
   - Standalone command example:
     ```
     git-sync \
       --repo=git@ssh.dev.azure.com:v3/your-org/your-project/your-repo \
       --branch=main \
       --root=/git \
       --ssh-key-file=/secrets/id_ed25519 \
       --ssh-known-hosts=true \
       --ssh-known-hosts-file=/secrets/known_hosts \
       --wait=30
     ```

5. **Integrate into Kubernetes (for GitOps)**:
   - Create a Kubernetes Secret with your private key and known_hosts:
     ```
     kubectl create secret generic azure-devops-ssh \
       --from-file=ssh-private-key=/path/to/id_ed25519 \
       --from-file=known_hosts=/path/to/known_hosts
     ```
     - Ensure the private key has mode 0400 (read-only for owner) in the secret for security.
   - Update your Deployment YAML:
     - Add a volume for the secret:
       ```yaml
       volumes:
       - name: ssh-secret
         secret:
           secretName: azure-devops-ssh
           items:
           - key: ssh-private-key
             path: id_ed25519
             mode: 0400
           - key: known_hosts
             path: known_hosts
       ```
     - In the git-sync container:
       ```yaml
       containers:
       - name: git-sync
         image: registry.k8s.io/git-sync/git-sync:v4.2.4  # Or latest version
         args:
         - --repo=git@ssh.dev.azure.com:v3/your-org/your-project/your-repo
         - --branch=main
         - --root=/git
         - --ssh-key-file=/secrets/id_ed25519
         - --ssh-known-hosts=true
         - --ssh-known-hosts-file=/secrets/known_hosts
         - --wait=30
         volumeMounts:
         - name: ssh-secret
           mountPath: /secrets
           readOnly: true
         - name: git-repo-volume  # Shared with your main container
           mountPath: /git
       ```
   - Apply the Deployment and verify the pod starts without auth errors.

6. **Test and Troubleshoot**:
   - Test locally: `GIT_SSH_COMMAND="ssh -i /path/to/id_ed25519" git clone git@ssh.dev.azure.com:v3/your-org/your-project/your-repo`.
   - Check git-sync logs for issues (e.g., "permission denied" means key mismatch; "host key verification failed" means missing known_hosts).
   - If submodules are involved, ensure recursive flags or additional configs are added.
   - Rotate keys periodically for security—generate new ones and update Azure DevOps/secrets as needed.

This setup ensures reliable, expiration-free syncing. If your org has restrictions on SSH, fall back to PATs with automation for rotation (e.g., via scripts or CI/CD).