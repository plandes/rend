-- Browse to theUrlList adding each as a tab and showing the window set the
-- window extents of it.  A window with a single tab for this URL does not yet
-- exist, create one.
on showSafariMulti(theUrlList, x, y, width, height)
    log("showSafariMulti")
    tell application "Safari"
	--activate
	set targetWindowFound to false
	set targetWindow to ""
	set matchTabs to {}
	repeat with thisWindow in windows
	    --set numTabs to count of tabs of thisWindow
	    repeat with queryUrl in theUrlList
		set queryUrl to queryUrl as text
		log("search for query: " & queryUrl)
		repeat with thisTab in tabs of thisWindow
		    set thisUrl to URL of thisTab
		    set matches to (queryUrl = thisUrl)
		    log("compare: " & queryUrl & " == " & thisUrl & ", matches: " & matches)
		    if (matches) then
			log("adding tab " & thisUrl)
			copy thisTab to end of matchTabs
		    end if
		end repeat
	    end repeat
	    if (count of theUrlList = count of matchTabs) then
		log("found match tabs: " & count of theUrlList & ", " & count of matchTabs)
		set targetWindowFound to true
		set targetWindow to thisWindow
		exit repeat
	    end if
	end repeat
	if targetWindowFound then
	    set urlIx to 0
	    repeat with thisTab in matchTabs
		set urlIx to urlIx + 1
		set theUrl to item urlIx of theUrlList
		log("setting url in " & theUrl)
		set URL of thisTab to theUrl
	    end repeat
	    tell targetWindow
		set visible to true
		set index to 1
	    end tell
	else
	    set theDoc to make new document
	    tell front window
		set theOldTab to ""
		repeat with queryUrl in theUrlList
		    if (theOldTab = "")
			set theOldTab to front tab
		    else
			set theOldTab to make new tab
		    end if
		    set URL of theOldTab to queryUrl
		end repeat
	    end tell
	end if
	set theBounds to {x, y, width, height}
	set the bounds of the window 1 to theBounds
    end tell
end showSafariMulti
