#!/usr/bin/env sh
# Dependencies flameshot, xclip, tesseract, tesseract-data-eng and tesseract-data-por
# yay -S xclip tesseract tesseract-data-eng tesseract-data-por

# Takes the Screenshot
flameshot gui -p /tmp/tesseract_screenshot.png

# Copy Text from Image
tesseract /tmp/tesseract_screenshot.png stdout -l eng+por | xclip -selection clipboard;

# Delete Last Screenshot
rm /tmp/tesseract_screenshot.png;

# Set the exit status based on whether the last command succeeded or failed
if [ $? -eq 0 ]; then
    exit 0  # Success
else
    exit 1  # Error
fi
