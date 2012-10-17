package net.relatedwork.client;

import com.google.gwt.user.client.rpc.IsSerializable;
import com.google.gwt.user.client.ui.SuggestOracle.Suggestion;

public class ItemSuggestion implements IsSerializable, Suggestion {

	private String s;

	// Required for IsSerializable to work
	public ItemSuggestion() {
	}

	// Convenience method for creation of a suggestion
	public ItemSuggestion(String s) {
		this.s = s;
	}

	public String getDisplayString() {
		return s;
	}

	public String getReplacementString() {
		return s;
	}
} // end inner class ItemSuggestionv