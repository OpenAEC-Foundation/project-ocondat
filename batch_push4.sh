#!/bin/bash
set -e
cd "/c/Users/rickd/Documents/GitHub/Project-Ocondat"
git config core.quotepath false

BATCH_SIZE=1000
BATCH_NUM=22

TOTAL=$(git ls-files --others --exclude-standard -z | tr '\0' '\n' | wc -l)
echo "Total remaining files: $TOTAL"

while true; do
    REMAINING=$(git ls-files --others --exclude-standard -z | tr '\0' '\n' | wc -l)
    if [ "$REMAINING" -eq 0 ]; then
        break
    fi

    BATCH_NUM=$((BATCH_NUM + 1))

    # Get batch of files into temp file
    TMPFILE="/c/Users/rickd/Documents/GitHub/Project-Ocondat/_batch_tmp.txt"
    git ls-files --others --exclude-standard -z | head -z -n $BATCH_SIZE > "$TMPFILE"

    # Check for large files and add them to .gitignore
    LARGE_FOUND=0
    while IFS= read -r -d '' file; do
        filesize=$(stat -c%s "$file" 2>/dev/null || echo 0)
        if [ "$filesize" -gt 99000000 ]; then
            echo "SKIPPING large file ($filesize bytes): $file"
            echo "$file" >> .gitignore
            git add .gitignore
            LARGE_FOUND=1
        fi
    done < "$TMPFILE"

    if [ "$LARGE_FOUND" -eq 1 ]; then
        rm -f "$TMPFILE"
        continue
    fi

    # Add the batch
    cat "$TMPFILE" | xargs -0 git add --
    rm -f "$TMPFILE"

    COUNT=$(git diff --cached --name-only | wc -l)
    if [ "$COUNT" -eq 0 ]; then
        echo "No files to commit, skipping..."
        continue
    fi

    echo ""
    echo "=== FASE $BATCH_NUM: Adding $COUNT files ($REMAINING remaining) ==="
    git commit -m "Fase $BATCH_NUM: Add $COUNT files ($REMAINING remaining)"

    echo "Pushing fase $BATCH_NUM..."
    git push origin master
    echo "=== FASE $BATCH_NUM COMPLETE ==="
done

rm -f "/c/Users/rickd/Documents/GitHub/Project-Ocondat/_batch_tmp.txt"

echo ""
echo "=== ALL DONE! ==="
echo "Total fases: $BATCH_NUM"
