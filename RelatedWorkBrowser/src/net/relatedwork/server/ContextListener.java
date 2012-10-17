package net.relatedwork.server;

import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;

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
    @SuppressWarnings("unchecked")
    public static EmbeddedReadOnlyGraphDatabase getNeo4jInstance(ServletContext servletContext){
            return (EmbeddedReadOnlyGraphDatabase) servletContext.getAttribute(NEO4J);
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
    }   
}    
