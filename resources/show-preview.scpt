-- Display a PDF file with Preview.app and set the window extents of it.
on showPreview(filename, x, y, width, height)
    --tell application "Finder" to open posixFile
    set command to "open " & filename
    do shell script command
    delay 0.1
    tell application "Preview"
         activate
         set theBounds to {x, y, width, height}
         set the bounds of the window 1 to theBounds
    end tell
    tell application "System Events"
         tell process "Preview"
                 click menu item "Single Page" of menu "View" of menu bar 1
                 click menu item "Continuous Scroll" of menu "View" of menu bar 1
         end tell
    end tell
end showPreview
