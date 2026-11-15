package br.uvr.leitura;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;

/**
 * O app inteiro é a página em assets/index.html, mostrada num WebView.
 * Os dados ficam no localStorage do WebView (pasta de dados do app).
 */
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle estado) {
        super.onCreate(estado);
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#14110e"));
        web.setOverScrollMode(WebView.OVER_SCROLL_NEVER);
        WebSettings cfg = web.getSettings();
        cfg.setJavaScriptEnabled(true);
        cfg.setDomStorageEnabled(true);   // localStorage
        cfg.setTextZoom(100);             // fonte grande do sistema não quebra o layout
        setContentView(web);
        if (estado == null) web.loadUrl("file:///android_asset/index.html");
        else web.restoreState(estado);
    }

    @Override
    protected void onSaveInstanceState(Bundle saida) {
        super.onSaveInstanceState(saida);
        web.saveState(saida);
    }

    // Voltar fecha a folha aberta (editar livro / backup); sem folha, sai do app.
    @Override
    public void onBackPressed() {
        web.evaluateJavascript("window.__voltar ? window.__voltar() : false", r -> {
            if (!"true".equals(r)) finish();
        });
    }
}
