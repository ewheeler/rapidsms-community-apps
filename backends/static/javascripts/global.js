jQuery(function() {


	/* insert the signal strength widgets
	 * in the header, after the rapidsms logo */
	var container = jQuery("#branding h1");


	/* fetches the current status data from the router
	 * (via the ajax app) and recurses in 30 seconds */
	var check = function() {
		jQuery.getJSON("/ajax/backends/status", function(data) {
			jQuery.cookie("backends-status", jQuery.toJSON(data));
			update_dom(data);

			/* poll again in thirty seconds */
			setTimeout(check, 30000);
		});
	}


	/* adds or updates the status spans in the header,
	 * to show the signal strength of each backend */
	var update_dom = function(data) {
		jQuery.each(data, function(backend, status) {

			/* look for an existing span for this
			 * backend, to update it rather than
			 * create a whole new one every time */
			var id = "be-signal-" + backend;
			var span = jQuery("#" + id, container);

			/* if no span exists for this backend,
			 * create it and update the _span_ var */
			if(span.size() == 0) {
				span = jQuery('<span id="' + id + '"></span>');
				container.append(span);
			}

			/* backends can return None (in Python) or omit the
			 * "signal" property altogether to indicate that the
			 * signal strength is unknown or not relevant */
			var signal = status["_signal"];
			if(signal == null) signal = "unknown";

			/* update the class (to update the icon) and
			 * add a tooltip with the new signal strength */
			span.attr("title", "Signal Strength for " + status["_title"] + ": " + signal);
			span.attr("class", "signal s-" + signal);

			/* insert the full status into the
			 * span, to be shown on hover via css */
			var items = [];
			jQuery.each(status, function(key, val) {
				if(key.substr(0,1) != "_") {
					items.push("<li><span>" + key + ":</span> " + val + "</li>");
				}
			})

			if(items.length > 0) {
				span.html('<ul><li class="title">' + status["_title"] + "</li>" + items.join("") + "</ul>");

			/* if there aren't any properties to,
			 *  show, don't bother creating the <ul> */
			} else {
				span.html("");
			}
		});

		var num = jQuery("span.signal", container).size();
		container.attr("class", "backends-" + num);
	}


	/* update asap (dom ready) from the cookie
	 * (if it exists) to avoid the ajax delay */
	var data = jQuery.cookie("backends-status");
	if(data) update_dom(jQuery.secureEvalJSON(data));


	/* poll the server in five seconds, to avoid hitting
	 * it if the user is only browsing past this view */
	 setTimeout(check, 5000);
});
