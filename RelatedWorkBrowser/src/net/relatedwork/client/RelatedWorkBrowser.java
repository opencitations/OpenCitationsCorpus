package net.relatedwork.client;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.KeyCodes;
import com.google.gwt.event.dom.client.KeyUpEvent;
import com.google.gwt.event.dom.client.KeyUpHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.SuggestBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.ValueBoxBase;

/**
 * Entry point classes define <code>onModuleLoad()</code>.
 */
public class RelatedWorkBrowser implements EntryPoint {

	/**
	 * this will mainly talk to autosuggest via RPC call.
	 */

	/**
	 * This is the entry point method.
	 */
	public void onModuleLoad() {
		final Button sendButton = new Button("search");
		
	    ItemSuggestOracle oracle = new ItemSuggestOracle();      
	    final SuggestBox sb = new SuggestBox(oracle);
	    sb.setText("search for papers, authors, or anything else related to science");
		sb.addStyleName("searchBox");
	       
	       // Add it to the root panel.
		sendButton.addStyleName("sendButton");

		// Add the nameField and sendButton to the RootPanel
		// Use RootPanel.get() to get the entire body element
		//RootPanel.get("nameFieldContainer").add(nameField);
		RootPanel.get("sendButtonContainer").add(sendButton);
	    RootPanel.get("nameFieldContainer").add(sb);

		
		// Focus the cursor on the name field when the app loads
		sb.setFocus(true);

		// Create a handler for the sendButton and nameField
		class MyHandler implements ClickHandler, KeyUpHandler {
			/**
			 * Fired when the user clicks on the sendButton.
			 */
			public void onClick(ClickEvent event) {
			}

			/**
			 * Fired when the user types in the nameField.
			 */
			public void onKeyUp(KeyUpEvent event) {
				if (event.getNativeKeyCode() == KeyCodes.KEY_ENTER) {
				}
			}
		}

		// Add a handler to send the name to the server
		MyHandler handler = new MyHandler();
		sendButton.addClickHandler(handler);
		sb.addStyleName("searchBox");

	}
}
