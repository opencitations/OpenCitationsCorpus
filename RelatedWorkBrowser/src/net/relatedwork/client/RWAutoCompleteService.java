package net.relatedwork.client;

import com.google.gwt.core.client.GWT;
import com.google.gwt.user.client.rpc.RemoteService;
import com.google.gwt.user.client.rpc.ServiceDefTarget;
import com.google.gwt.user.client.ui.SuggestOracle;

public interface RWAutoCompleteService extends RemoteService {
	public static class Util {
		public static RWAutoCompleteServiceAsync getInstance() {
			RWAutoCompleteServiceAsync instance = (RWAutoCompleteServiceAsync) GWT
					.create(RWAutoCompleteService.class);
			ServiceDefTarget target = (ServiceDefTarget) instance;
			target.setServiceEntryPoint("/autocomplete/suggest");
			return instance;
		}
	}

	public SuggestOracle.Response getSuggestions(SuggestOracle.Request req);
}
