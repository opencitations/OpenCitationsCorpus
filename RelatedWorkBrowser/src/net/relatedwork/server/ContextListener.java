package net.relatedwork.server;

import java.util.Comparator;
import java.util.HashMap;

import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;

import org.neo4j.graphdb.Node;
import org.neo4j.kernel.EmbeddedReadOnlyGraphDatabase;
/**
 * this context listener is supposed to help let objects in the server live even though the request is processed
 * remember to register context in web.xml
 * 
 * @author rpickhardt
 *
 */

public class ContextListener implements ServletContextListener {

    private static final String NEO4J = "neo4j";
    private static final String SUGGESTTREE = "suggest-tree";
    
    @SuppressWarnings("unchecked")
    public static EmbeddedReadOnlyGraphDatabase getNeo4jInstance(ServletContext servletContext){
            return (EmbeddedReadOnlyGraphDatabase) servletContext.getAttribute(NEO4J);
    }  
    
    public static SuggestTree<Double> getAutoCompleteTree(ServletContext servletContext){
            return (SuggestTree<Double>) servletContext.getAttribute(SUGGESTTREE);
    } 
    
    @Override
    public void contextDestroyed(ServletContextEvent arg0) {
    	getNeo4jInstance(arg0.getServletContext()).shutdown();
    }

    @Override
    public void contextInitialized(ServletContextEvent servletContextEvent) {
    		EmbeddedReadOnlyGraphDatabase graphDB = new EmbeddedReadOnlyGraphDatabase("/var/lib/datasets/rawdata/relatedwork/db_folder");       
            ServletContext servletContext = servletContextEvent.getServletContext();
            servletContext.setAttribute(NEO4J, graphDB);
            
            SuggestTree<Double> tree = buildSuggestTree(graphDB);
            servletContext.setAttribute(SUGGESTTREE, tree);
    }

	private SuggestTree<Double> buildSuggestTree(
			EmbeddedReadOnlyGraphDatabase graphDB) {
		
        Comparator<Double> c = new Comparator<Double>() {
            public int compare(Double e1,
                               Double e2) {
                return -e1.compareTo(e2);
            } 
                };              
                SuggestTree<Double> suggestTree = new SuggestTree<Double>(7, c);     
                HashMap<String, Double> ranks = new HashMap<String, Double>();

		for (Node n:graphDB.getAllNodes()){
			if (n.hasProperty("pageRankValue")){
				if (n.hasProperty("title")){
					String tmp = (String)n.getProperty("title");
					Double pr = (Double)n.getProperty("pageRankValue");
					ranks.put(tmp, pr);
				}
				if (n.hasProperty("name")){
					String tmp = (String)n.getProperty("name");
					Double pr = (Double)n.getProperty("pageRankValue");
					ranks.put(tmp, pr);
				}
			}
		}
		suggestTree.build(ranks);
		return suggestTree;
	}   
}    
