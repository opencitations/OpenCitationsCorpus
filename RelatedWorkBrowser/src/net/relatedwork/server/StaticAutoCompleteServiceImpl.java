package net.relatedwork.server;

import java.util.ArrayList;
import java.util.List;

import net.relatedwork.client.ItemSuggestion;
import net.relatedwork.client.RWAutoCompleteService;

import com.google.gwt.user.client.ui.SuggestOracle;
import com.google.gwt.user.server.rpc.RemoteServiceServlet;

public class StaticAutoCompleteServiceImpl extends RemoteServiceServlet implements RWAutoCompleteService {
	  
	  
	private static final long serialVersionUID = 4017728426934645380L;

	public SuggestOracle.Response getSuggestions(SuggestOracle.Request req) {
	      
	       // req has request properties that you can use to perform a db search
	       // or some other query. Then populate the suggestions up to req.getLimit() and
	       // return in a SuggestOracle.Response object.
	       SuggestOracle.Response resp = new SuggestOracle.Response();
	      
	       List<ItemSuggestion> suggestions = new ArrayList<ItemSuggestion>();
	       suggestions.add(new ItemSuggestion("Heinrich Hartmann"));
	       suggestions.add(new ItemSuggestion("Rene Pickhardt"));
	       suggestions.add(new ItemSuggestion("Efficient Graph Models for Retrieving Top-k News Feeds from Ego Networks"));
	       suggestions.add(new ItemSuggestion("Stability conditions on K3 surfaces"));
	      
	       resp.setSuggestions(suggestions);
	       return resp;
	   }
	}
