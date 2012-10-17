package net.relatedwork.server;

import java.util.ArrayList;
import java.util.List;

import net.relatedwork.client.ItemSuggestion;
import net.relatedwork.client.RWAutoCompleteService;

import org.neo4j.graphdb.Node;
import org.neo4j.kernel.EmbeddedGraphDatabase;
import org.neo4j.kernel.EmbeddedReadOnlyGraphDatabase;

import com.google.gwt.user.client.ui.SuggestOracle;
import com.google.gwt.user.server.rpc.RemoteServiceServlet;
/**
 * 
 * @author rpickhardt
 *
 */
public class StaticAutoCompleteServiceImpl extends RemoteServiceServlet
		implements RWAutoCompleteService {

	private static final long serialVersionUID = 4017728426934645380L;

	public SuggestOracle.Response getSuggestions(SuggestOracle.Request req) {

		// req has request properties that you can use to perform a db search
		// or some other query. Then populate the suggestions up to
		// req.getLimit() and
		// return in a SuggestOracle.Response object.
		SuggestOracle.Response resp = new SuggestOracle.Response();
		String query = req.getQuery();

		List<ItemSuggestion> suggestions = getSuggestions(query, 5);

		resp.setSuggestions(suggestions);
		return resp;
	}

	private List<ItemSuggestion> getSuggestions(String query, int k) {
		List<ItemSuggestion> suggestions = new ArrayList<ItemSuggestion>();
		
		//we can call getServletContext since we are extending RemoteServiceServlet
		EmbeddedReadOnlyGraphDatabase graphDB = ContextListener.getNeo4jInstance(getServletContext());
		
		if (graphDB==null)return null;
		
		for (Node n:graphDB.getAllNodes()){
			if (n.hasProperty("title")){
				String tmp = (String)n.getProperty("title");
				if (tmp.startsWith(query)){
					suggestions.add(new ItemSuggestion(tmp));
				}
			}
			if (n.hasProperty("name")){
				String tmp = (String)n.getProperty("name");
				if (tmp.startsWith(query)){
					suggestions.add(new ItemSuggestion(tmp));
				}
			}
			if (suggestions.size()>k){
				return suggestions;
			}
		}
		return suggestions;
	}
}
