package neo4jHelper;

import java.util.HashMap;
import java.util.HashSet;

import org.apache.lucene.search.Sort;
import org.apache.lucene.search.SortField;
import org.neo4j.graphdb.Direction;
import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.Relationship;
import org.neo4j.graphdb.Transaction;
import org.neo4j.graphdb.index.Index;
import org.neo4j.graphdb.index.IndexHits;
import org.neo4j.index.impl.lucene.LuceneIndex;
import org.neo4j.index.lucene.QueryContext;
import org.neo4j.kernel.EmbeddedGraphDatabase;

public class UnderstandDatabase {
	private EmbeddedGraphDatabase graphDB;
	public UnderstandDatabase(String path){
		graphDB = new EmbeddedGraphDatabase(path);
	}
	
	public EmbeddedGraphDatabase getGraphDB() {
		return graphDB;
	}

	public void setGraphDB(EmbeddedGraphDatabase graphDatabaseService) {
		this.graphDB = graphDatabaseService;
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

	public HashMap<String,Double> showPageRankValues(){
		HashMap<String,Double> properties= new HashMap<String, Double>();
		for(Node n:graphDB.getAllNodes()){
			if (!n.hasProperty("pageRankValue"))continue;
			Double pr = (Double)n.getProperty("pageRankValue");
			String name = (String)n.getProperty("label");
			if (pr>2)	
			System.out.println(name + "\t" + pr);
			else continue;
			properties.put(name, pr);
		}
		return properties;		
	}
	
	public void shutDown() {
		graphDB.shutdown();		
	}

	public void search(String string) {
		for (Node n:graphDB.getAllNodes()){
			if (n.hasProperty("title")){	
				String label = (String)n.getProperty("title");
				if (label.contains(string))
					System.out.println(label);
			}
			
		}
	}
	public void putPageRankToLucence(){
		Index<Node> ix = graphDB.index().forNodes("pageRank");
		
		Transaction tx = graphDB.beginTx();
		try {
			int cnt = 0;
			for (Node n:graphDB.getAllNodes()){
				if (n.hasProperty("pageRankValue")){
					if (n.hasProperty("title")){
						//String tmp = (String)n.getProperty("title");
						Double pr = - (Double)n.getProperty("pageRankValue");
						ix.add(n, "pr", pr);
					}
					if (n.hasProperty("name")){
						//String tmp = (String)n.getProperty("name");
						Double pr = - (Double)n.getProperty("pageRankValue");
						ix.add(n, "pr", pr);
					}
				}
				if (cnt++%10000==0){
					System.out.println(cnt);
					tx.success();
					tx.finish();
					tx = graphDB.beginTx();
				}
			}
			tx.success();
		}catch (Exception e){
			e.printStackTrace();
		}finally{
			tx.finish();
		}
	}
	
	public void getNodesWithHighPageRank(){
		Index<Node> ix = graphDB.index().forNodes("pageRank");
		QueryContext c = new QueryContext(new Object());
		
		IndexHits<Node> hits;
        hits = ix.query("pr", new QueryContext("*").sort("pr").top(200));
        for (Node hit: hits){
        	System.out.println(hit.getProperty("pageRankValue"));
        }
	}

	public void searchBenchMark() {
		Index<Node> test = graphDB.index().forNodes("prsearch_idx");
		((LuceneIndex<Node>) test).setCacheCapacity("title", 300000);

		for (int j = 1; j < 3; j++) {
			System.out.println("\n\n\t\t" + j + " round.\n");
			String[] array = { "Witten*", "Lehn*", "Hartmann*", "Vois*",
					"*Peter", "Scholz*", "Leib*", "Maier*", "Hitchin*",
					"Higgs*" };

			for (int i = 0; i < 10; i++) {
				Sort s = new Sort();
				s.setSort(new SortField("pr", SortField.DOUBLE, true));
				long start = System.currentTimeMillis();
				IndexHits<Node> res = test.query(new QueryContext("title:"
						+ array[i]).sort(s));
				if (res == null)
					continue;
				for (Node n : res) {
					if (n.hasProperty("name")) {
						// System.out.println((Double)n.getProperty("pageRankValue")
						// + "\t" +(String)n.getProperty("name"));
					}
					if (n.hasProperty("title")) {
						// System.out.println((Double)n.getProperty("pageRankValue")
						// + "\t" +(String)n.getProperty("title"));
					}
				}
				long end = System.currentTimeMillis();
				System.out.println("search for: " + array[i]
						+ "\nindexlookup: " + (end - start)
						+ "ms \t number of elements: " + res.size() + "\n");
			}
		}		
	}
	public void testAuthorIndex(String id){
		Index<Node> index = graphDB.index().forNodes("author_idx");

		
		String q = id.replace(' ', '?');
		IndexHits<Node> hits = index.get("name", "*");
		//if (author == null)return;
for(Node author:hits){
		System.out.println( (String) author.getProperty("name"));		
		
		for (Relationship rel:author.getRelationships()){
			System.out.println(rel.getType().name());
			Node otherNode = rel.getOtherNode(author);
			if (otherNode.hasProperty("title")){// i found a paper
				System.out.println((String)otherNode.getProperty("title"));
			}
		}
}
	}
}
