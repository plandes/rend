-- parse the page number from the Preview title: "X.pdf Page Y of Z"
on parseWindowName(theName)
    set pgIdx to (offset of "Page" in theName) + 5
    set pgStr to (characters pgIdx thru -1 of theName) as string
    set endIdx to (offset of " " in pgStr) - 1
    return (characters 1 thru endIdx of pgStr) as string
end parseWindowName

-- return the page number as a string from Preview.app
on getPageNumber()
    set theName to null
    set currentPageNumber to null
    tell application "System Events"
        tell process "Preview"
	    if count of windows > 0 then
		set theName to name of window 1
	    end if
	end tell
    end tell
    if theName is not null then
	set currentPageNumber to parseWindowName(theName)
    end if
    log "window title: " & theName
    log "current page number: " & currentPageNumber
    return currentPageNumber
end getPageNumber

-- display a PDF file with Preview.app and set the window extents of it.
on showPreview(filename, x, y, width, height, updatePage)
    set currentPageNumber to null
    set maybeChangedPageNumber to null
    set maybe to null
    if updatePage then
	set currentPageNumber to getPageNumber()
    end if
    set command to "open " & filename
    do shell script command
    delay 0.1
    tell application "Preview"
        activate
        set theBounds to {x, y, width, height}
        set the bounds of the window 1 to theBounds
    end tell
    if updatePage then
	set maybeChangedPageNumber to getPageNumber()
    end if
    log "page changed from " & currentPageNumber & " to " & maybeChangedPageNumber
    -- only chage page if it changes to avoid latency of changing it via GUI
    if currentPageNumber = maybeChangedPageNumber then
	set currentPageNumber to null
    else
	set currentPageNumber to maybeChangedPageNumber
    end if
    tell application "System Events"
        tell process "Preview"
            click menu item "Single Page" of menu "View" of menu bar 1
            click menu item "Continuous Scroll" of menu "View" of menu bar 1
	    if currentPageNumber is not null then
		keystroke "g" using {option down, command down} -- Go menu : Go to Page…
		log "going to page: " & currentPageNumber
		keystroke currentPageNumber
		delay 0.1
		keystroke return
	    end if
        end tell
    end tell
end showPreview
