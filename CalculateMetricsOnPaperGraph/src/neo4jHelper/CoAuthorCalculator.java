package neo4jHelper;

import java.util.HashMap;

import org.neo4j.graphdb.Direction;
import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.Relationship;
import org.neo4j.graphdb.Transaction;

import utils.IOHelper;

/**
 * This class calculates two things for every author in the data base.
 * 
 * 1. the count of how often every pair of nodes have been coauthored papers
 * 
 * 2. the authors this particular author likes to cite.
 * @author rpickhardt
 *
 */

public class CoAuthorCalculator extends Calculator {
	//TODO: decide if tanimoto or absolute score should be used! I think absolutes are better
	public void calculateCoAuthors(int transactionThreshhold){
		Transaction tx = graphDB.beginTx();
		try {
			int transactionCount = 0;
			for (Node author:graphDB.getAllNodes()){
				if (!author.hasProperty("name"))continue;
				HashMap<Node, Integer> coAuthors = new HashMap<Node, Integer>();
				for (Relationship rel: author.getRelationships(RelationshipTypes.AUTHOROF)){
					Node paper = rel.getOtherNode(author);
					for (Relationship coAuthorRel: paper.getRelationships(RelationshipTypes.AUTHOROF)){
						Node coAuthor = coAuthorRel.getOtherNode(paper);
						if (coAuthor.getId()==author.getId())continue;
	
						if (coAuthors .containsKey(coAuthor))
							coAuthors.put(coAuthor, coAuthors.get(coAuthor) + 1);
						else
							coAuthors.put(coAuthor, 1);
	
					}
				}
				for (Node coAuthor: coAuthors.keySet()){
					Relationship coAuthorRel = author.createRelationshipTo(coAuthor, RelationshipTypes.CO_AUTHOR_COUNT);
					coAuthorRel.setProperty(DBRelationshipProperties.CO_AUTHOR_COUNT,coAuthors.get(coAuthor));
					
					if (++transactionCount % transactionThreshhold == 0){
						tx.success();
						tx.finish();
						tx = graphDB.beginTx();
						IOHelper.log(transactionCount + " coAuthor relations have been inserted so far");
						System.out.println("current relation's count is " + coAuthors.get(coAuthor));			
					}					
				}			
			}
			tx.success();
		}finally{
			tx.finish();
		}
	}
	
	public void calculateLikesToCiteAuthors(int transactionThreshhold){
		Transaction tx = graphDB.beginTx();
		try {
			int transactionCount = 0;
			for (Node author:graphDB.getAllNodes()){
				if (!author.hasProperty("name"))continue; // only want to work on authors
				HashMap<Node, Integer> citedAuthors = new HashMap<Node, Integer>();
				for (Relationship rel:author.getRelationships(RelationshipTypes.AUTHOROF)){
					Node paper = rel.getOtherNode(author);
					if (paper.hasProperty("title")){// i found a paper
						//find cited authors
						for (Relationship citedPaperRel: paper.getRelationships(RelationshipTypes.CITES,Direction.OUTGOING)){
							Node citedPaper = citedPaperRel.getOtherNode(paper);
							if (citedPaper.hasProperty("title")){
								for (Relationship citedAuthorRel: citedPaper.getRelationships(RelationshipTypes.AUTHOROF)){
									Node citedAuthor = citedAuthorRel.getOtherNode(citedPaper);
									if (citedAuthor.getId()==author.getId())continue;
									if (citedAuthor.hasProperty("name")){
										if (citedAuthors.containsKey(citedAuthor))
											citedAuthors.put(citedAuthor, citedAuthors.get(citedAuthor) + 1);
										else
											citedAuthors.put(citedAuthor, 1);
									}
								}
							}
						}
					}
				}
				for (Node citedAuthor: citedAuthors.keySet()){
					//TODO: exchange relationship types and properties
					Relationship coAuthorRel = author.createRelationshipTo(citedAuthor, RelationshipTypes.CO_AUTHOR_COUNT);
					coAuthorRel.setProperty(DBRelationshipProperties.CO_AUTHOR_COUNT,citedAuthors.get(citedAuthor));
					
					if (++transactionCount % transactionThreshhold == 0){
						tx.success();
						tx.finish();
						tx = graphDB.beginTx();
						IOHelper.log(transactionCount + " citedAuthor relations have been inserted so far");
						System.out.println("current relation's count is " + citedAuthors.get(citedAuthor));			
					}					
				}			
			}
			tx.success();
		}finally{
			tx.finish();
		}
	}	
}
