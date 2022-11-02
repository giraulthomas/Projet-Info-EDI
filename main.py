# -*- coding: utf-8 -*-
from flask import Flask, url_for, request, render_template, redirect, flash
from fonction import *

# ------------------
# application Flask
# ------------------
app = Flask(__name__)
app.secret_key = 'the random string'

# ---------------------------------------
# les différentes pages (fonctions VUES)
# ---------------------------------------
# une page index avec des liens vers les différentes pages d'exemple d'utilisation de Flask
@app.route('/')
@app.route('/index')
def index():
    title = "index.LEGO"
    return render_template('index.html', title=title)


@app.route('/agiGREEN')
def agiGREEN():
    title = "AgiGreen"
    return render_template('page agiGREEN.html', title=title)


@app.route('/agiLEAN')
def agiLEAN():
    title = "AgiLean"
    return render_template('page agiLEAN.html', title=title)


@app.route('/agiLOG')
def agiLOG():
    title = "AgiLog"
    return render_template('page agiLOG.html', title=title)


@app.route('/agiPART')
def agiPART():
    title = "AgiPart"
    return render_template('page agiPART.html', title=title)


@app.route('/commandes')
def commandes():
    title = "Commande de kit"
    return render_template('page commande.html', title=title)


@app.route('/stock')
def stock():
    title = "Stock AgiLog"
    liste_stock = affichage_stock()
    liste_noms_entete = ["Désignation", "Code article", "Fournisseur", "Stock", "Seuil de commande"]
    liste_noms_case = ["designation", "code_article", "nom", "stock", "seuil_commande"]
    return render_template('page stock.html', title=title, liste_stock=liste_stock, liste_noms_entete=liste_noms_entete,
                           liste_noms_case=liste_noms_case)


@app.route('/init_stock', methods=['GET', 'POST'])
def init_stock():
    title = "Initialisation Stock AgiLog"
    liste_stock = affichage_stock()
    liste_entete = ["Désignation","Code article"]
    liste_case   = ["designation","code_article"]
    liste_entete_input = ["Stock","Seuil de commande","Délai","Niveau de recomplétion"]
    liste_case_input   = ["stock","seuil_commande",  "delai","niveau_recompletion"]
    if request.method == 'POST':
        liste_id=[piece["id"] for piece in liste_stock]
        dict_pieces={}
        for id_piece in liste_id:
            dict_piececourante={}
            for case_input in liste_case_input:
                value=request.form[str(id_piece)+"-"+case_input]
                if value=="None":
                    value=None
                elif case_input in ["stock","seuil_commande","niveau_recompletion"]:
                    try:
                        value=int(value)
                    except:
                        flash(case_input+" doit être un entier")
                        return redirect(url_for('init_stock'))
                dict_piececourante[case_input]=value
            dict_pieces[id_piece]=dict_piececourante
        try:
            sql_init_stock(dict_pieces)
            flash("Stock initiés!")
        except:
            flash("Problème d'initialisation")
        return redirect(url_for('init_stock'))
    return render_template('page initialisation stock.html', title=title, liste_stock=liste_stock, liste_entete=liste_entete,
                           liste_case=liste_case,liste_entete_input=liste_entete_input,liste_case_input=liste_case_input)


# ---------------------------------------
# pour lancer le serveur web local Flask
# ---------------------------------------
if __name__ == '__main__':
    app.run(debug=True)