# Setting up fb-ai Command (Optional)

To call `fb-ai` from anywhere without `./`, you can add it to your PATH:

## Option 1: User bin directory (Recommended)

```bash
# Create wrapper script
mkdir -p ~/bin

cat << 'EOF' > ~/bin/fb-ai
#!/bin/bash
# fb-ai wrapper - calls the actual script from project directory
cd /home/dominick/workspace/fantasy-baseball-ai && .github/prompts/fb-ai "$@"
EOF

chmod +x ~/bin/fb-ai

# Add to PATH (if not already there)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Now you can use just `fb-ai` from anywhere!

## Option 2: Use from project root

If you don't want to set up PATH, just use it from the project root:

```bash
cd /home/dominick/workspace/fantasy-baseball-ai
./fb-ai
```

The symlink `fb-ai` in the project root points to `.github/prompts/fb-ai`.

## Verify Installation

```bash
which fb-ai          # Should show ~/bin/fb-ai
fb-ai --help         # Should show help menu
fb-ai --when         # Should check game times
```

## Notes

- The actual script is located at `.github/prompts/fb-ai`
- The wrapper ensures it runs from the correct project directory
- Works from any directory once PATH is set up
