on parseWindowName(theName)
    set pgIdx to (offset of "Page" in theName) + 5
    set pgStr to (characters pgIdx thru -1 of theName) as string
    set endIdx to (offset of " " in pgStr) - 1
    return (characters 1 thru endIdx of pgStr) as string
end parseWindowName

-- Display a PDF file with Preview.app and set the window extents of it.
on showPreview(filename, x, y, width, height, updatePage)
    set currentPageNumber to null
    set theName to null
    if updatePage then
	tell application "System Events"
            tell process "Preview"
		if count of windows > 0 then
		    set theName to name of window 1
		end if
	    end tell
	end tell
    end if
    if theName is not null then
	set currentPageNumber to parseWindowName(theName)
    end if
    log "window title: " & theName
    log "current page number: " & currentPageNumber
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
	    if currentPageNumber is not null then
		keystroke "g" using {option down, command down} -- Go menu : Go to Page…
		log "going to page: " & currentPageNumber
		keystroke currentPageNumber
		keystroke return
	    end if
        end tell
    end tell
end showPreview
