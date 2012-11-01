package net.relatedwork.client.gin;

import com.gwtplatform.mvp.client.gin.AbstractPresenterModule;
import com.gwtplatform.mvp.client.gin.DefaultModule;
import net.relatedwork.client.place.ClientPlaceManager;
import net.relatedwork.client.MainPresenter;
import net.relatedwork.client.MainView;
import net.relatedwork.client.place.DefaultPlace;
import net.relatedwork.client.place.NameTokens;
import net.relatedwork.client.staticpresenter.ImprintPresenter;
import net.relatedwork.client.staticpresenter.ImprintView;
import net.relatedwork.client.FooterPresenter;
import net.relatedwork.client.FooterView;
import net.relatedwork.client.layout.BreadcrumbsPresenter;
import net.relatedwork.client.layout.BreadcrumbsView;
import net.relatedwork.client.HomePresenter;
import net.relatedwork.client.HomeView;
<<<<<<< HEAD
import net.relatedwork.client.Discussions.CommentPresenter;
import net.relatedwork.client.Discussions.CommentView;
=======
import net.relatedwork.client.staticpresenter.AboutPresenter;
import net.relatedwork.client.staticpresenter.AboutView;
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 04626ff... Added about presenter, yeah!!! ;)
=======
import net.relatedwork.client.staticpresenter.NotYetImplementedPresenter;
import net.relatedwork.client.staticpresenter.NotYetImplementedView;
>>>>>>> 2c450ac... auto completion works theoretically. still need to clean up code
=======
import net.relatedwork.client.staticpresenter.DataPresenter;
import net.relatedwork.client.staticpresenter.DataView;
<<<<<<< HEAD
>>>>>>> 82b95eb... Footer: Data Preseter works
=======
import net.relatedwork.client.staticpresenter.LicensePresenter;
import net.relatedwork.client.staticpresenter.LicenseView;
<<<<<<< HEAD
>>>>>>> 05445a3... Footer: License Preseter works
=======
import net.relatedwork.client.content.AuthorPresenter;
import net.relatedwork.client.content.AuthorView;
<<<<<<< HEAD
>>>>>>> 2218b23... included an author presenter and started workflow. we need ListPresenter
=======
import net.relatedwork.client.tools.ListPresenter;
import net.relatedwork.client.tools.ListView;
<<<<<<< HEAD
>>>>>>> 381517a... added TEMPLATED list presenter and displayed author list like that also created interface IsRenderable
=======
import net.relatedwork.client.login.LoginPopupPresenter;
import net.relatedwork.client.login.LoginPopupView;
import net.relatedwork.client.header.HeaderPresenter;
import net.relatedwork.client.header.HeaderView;
>>>>>>> f0097d5... Added header presenter and Login popup presenter.

public class ClientModule extends AbstractPresenterModule {

	@Override
	protected void configure() {
		install(new DefaultModule(ClientPlaceManager.class));

		bindPresenter(MainPresenter.class, MainPresenter.MyView.class,
				MainView.class, MainPresenter.MyProxy.class);

		bindConstant().annotatedWith(DefaultPlace.class).to(NameTokens.main);

		bindPresenter(FooterPresenter.class, FooterPresenter.MyView.class,
				FooterView.class, FooterPresenter.MyProxy.class);

		bindPresenter(ImprintPresenter.class, ImprintPresenter.MyView.class,
				ImprintView.class, ImprintPresenter.MyProxy.class);

		bindPresenterWidget(BreadcrumbsPresenter.class,
				BreadcrumbsPresenter.MyView.class, BreadcrumbsView.class);

		bindPresenterWidget(HomePresenter.class, HomePresenter.MyView.class,
				HomeView.class);

<<<<<<< HEAD
		bindPresenterWidget(CommentPresenter.class,
				CommentPresenter.MyView.class, CommentView.class);
=======
		bindPresenter(AboutPresenter.class, AboutPresenter.MyView.class,
				AboutView.class, AboutPresenter.MyProxy.class);
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 04626ff... Added about presenter, yeah!!! ;)
=======

		bindPresenterWidget(NotYetImplementedPresenter.class,
				NotYetImplementedPresenter.MyView.class,
				NotYetImplementedView.class);
>>>>>>> 2c450ac... auto completion works theoretically. still need to clean up code
=======

		bindPresenter(DataPresenter.class, DataPresenter.MyView.class,
				DataView.class, DataPresenter.MyProxy.class);
<<<<<<< HEAD
>>>>>>> 82b95eb... Footer: Data Preseter works
=======

		bindPresenter(LicensePresenter.class, LicensePresenter.MyView.class,
				LicenseView.class, LicensePresenter.MyProxy.class);
<<<<<<< HEAD
>>>>>>> 05445a3... Footer: License Preseter works
=======

		bindPresenter(AuthorPresenter.class, AuthorPresenter.MyView.class,
				AuthorView.class, AuthorPresenter.MyProxy.class);
<<<<<<< HEAD
>>>>>>> 2218b23... included an author presenter and started workflow. we need ListPresenter
=======

		bindPresenterWidget(ListPresenter.class, ListPresenter.MyView.class,
				ListView.class);
<<<<<<< HEAD
>>>>>>> 381517a... added TEMPLATED list presenter and displayed author list like that also created interface IsRenderable
=======

		bindPresenterWidget(LoginPopupPresenter.class,
				LoginPopupPresenter.MyView.class, LoginPopupView.class);

		bindPresenter(HeaderPresenter.class, HeaderPresenter.MyView.class,
				HeaderView.class, HeaderPresenter.MyProxy.class);
>>>>>>> f0097d5... Added header presenter and Login popup presenter.
	}
}
