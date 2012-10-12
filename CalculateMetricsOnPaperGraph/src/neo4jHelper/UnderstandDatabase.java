package neo4jHelper;

import java.util.HashSet;

import org.neo4j.graphdb.Direction;
import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.Relationship;
import org.neo4j.kernel.EmbeddedGraphDatabase;

public class UnderstandDatabase {
	EmbeddedGraphDatabase graphDB;
	public UnderstandDatabase(String path){
		graphDB = new EmbeddedGraphDatabase(path);
	}
	
	public void countAverageNodeDegrees(int max){		
		int refEdges=0;
		int paperCnt=0;
		int authorCnt=0;
		int authorEdges=0;
		for(Node n:graphDB.getAllNodes()){
//			System.out.println("label:\t" + n.getProperty("label"));
			String label = (String)n.getProperty("label"); 
			if (label.equals("PAPER")||label.equals("AUTHOR"))continue;
			if (label.startsWith("paper_node"))paperCnt++;
			else if (label.startsWith("author_node"))authorCnt++;
			else continue;
			
			for (Relationship rel:n.getRelationships(Direction.OUTGOING)){
				if (rel.getType().name().equals("ref"))refEdges++;
				if (rel.getType().name().equals("author"))authorEdges++;
			}
		}
		
		System.out.println(paperCnt + "\tnumber of papers");
		System.out.println(refEdges + "\tnumber of citations ==> average amount of citations" +  refEdges / paperCnt);
		System.out.println(authorCnt + "\tnumber of authors");
		System.out.println(authorEdges + "\tnumber of papers authors contributed to  ==> average amount papers per author" +  authorEdges / authorCnt);
		
		System.out.println("co author graph is not explicitly available yet. so no statistics have been calculated");
		
	}

	public HashSet<String> listProperties(int max){
		HashSet<String> properties= new HashSet<String>();
		int cnt = 1;
		for(Node n:graphDB.getAllNodes()){
			for (String key:n.getPropertyKeys()){
				if (properties.contains(key))continue;
				properties.add(key);
				System.out.println(key);
				if(++cnt>max)break;
			}
		}
		return properties;
	}

	
	public void shutDown() {
		graphDB.shutdown();		
	}
}
