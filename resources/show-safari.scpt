-- Browse to theURL and showing the window set the window extents of it.  A
-- window with a single tab for this URL does not yet exist, create one.
on showSafari(theUrl, x, y, width, height)
    set targetWindowFound to false
    set targetWindow to ""
    log("browsing to " & theUrl)
    tell application "Safari"
	activate
	repeat with thisWindow in windows
	    set thisUrl to URL of current tab of thisWindow
	    set numTabs to count of tabs of thisWindow
	    log("iterating window: " & thisUrl & " with " & numTabs & " tab(s) open")
	    if (numTabs = 1) and (theUrl = thisUrl) then
	    	log("found window: " & thisUrl & " with " & numTabs & " tab(s) open")
		set targetWindow to thisWindow
		set targetWindowFound to true
	    end if
	end repeat
	if (targetWindowFound) then
	    log("target window found: " & thisUrl & " with " & numTabs & " tab(s) open")
	    tell targetWindow
	        set URL of document of targetWindow to theUrl
	        set visible to true
		set index to 1
	    end tell
	else
	    log("no window found so creating new")
	    set theDoc to make new document with properties {URL:theUrl}
	    repeat with thisWindow in windows
	    	if thisWindow's document is theDoc then set targetWindow to thisWindow
	    end repeat
	    log("target created with: " & URL of current tab of targetWindow)
	end if
	set theBounds to {x, y, width, height}
	set the bounds of the window 1 to theBounds
    end tell
end showSafari
