package net.relatedwork.client;

import com.google.gwt.user.client.rpc.AsyncCallback;
import com.google.gwt.user.client.ui.SuggestOracle;

public interface RWAutoCompleteServiceAsync {
	public void getSuggestions(SuggestOracle.Request req, AsyncCallback callback);
}