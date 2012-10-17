package net.relatedwork.client;

import com.google.gwt.user.client.rpc.AsyncCallback;
import com.google.gwt.user.client.ui.SuggestOracle;

/**
 * this is actuall where the caching will take place later
 * @author rpickhardt, http://developer-resource.blogspot.com/
 *
 */
public class ItemSuggestOracle extends SuggestOracle {

    public boolean isDisplayStringHTML() {
        return true;
    }

    public void requestSuggestions(SuggestOracle.Request req,SuggestOracle.Callback callback) {
        RWAutoCompleteService.Util.getInstance().getSuggestions(req, new ItemSuggestCallback(req, callback));
    }

    class ItemSuggestCallback implements AsyncCallback {

        private SuggestOracle.Request req;
        private SuggestOracle.Callback callback;

        public ItemSuggestCallback(SuggestOracle.Request _req,
                SuggestOracle.Callback _callback) {
            req = _req;
            callback = _callback;
        }

        public void onFailure(Throwable error) {
            callback.onSuggestionsReady(req, new SuggestOracle.Response());
        }

        public void onSuccess(Object retValue) {
            callback.onSuggestionsReady(req,
                    (SuggestOracle.Response) retValue);
        }
    }
}