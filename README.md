# tag-images

# How to Fork a Repository and Create a Codespace

## Step 1: Fork the Repository

1. Go to the original repository URL - https://github.com/mroswell/tag-images
2. Click the **Fork** button in the upper-right corner of the page
3. On the "Create a new fork" page:
   - Keep the default repository name (or rename if desired)
   - Leave "Copy the main branch only" checked
   - Click **Create fork**
4. Wait a few seconds—GitHub will redirect you to your new forked copy

You now have your own copy of the repository under your GitHub account. The URL will look like:
`https://github.com/YOUR-USERNAME/REPO-NAME`

## Step 2: Create a Codespace from Your Fork

1. Make sure you're on **your fork** (check that the URL shows your username.)
2. Click the green **Code** button
3. Select the **Codespaces** tab
4. Click **Create codespace on main**

GitHub will now build your Codespace. This may take a minute or two the first time.

## What You Now Have

- Your own fork of the repository (your personal copy on GitHub)
- A Codespace running from that fork (your development environment)
- Any changes you make and commit will save to **your fork**, not the original repository

## Saving Your Work

When you make changes in your Codespace:

1. Open the terminal (`` Ctrl + ` `` or **Terminal → New Terminal**)
2. Stage your changes: `git add .`
3. Commit with a message: `git commit -m "describe your changes"`
4. Push to your fork: `git push`

Your changes are now saved to your GitHub fork and will persist even after closing the Codespace.
