import sqlite3 as lite


def connection_bdd():
    """Connection au fichier bdd"""
    con = lite.connect('dev.db')
    con.row_factory = lite.Row
    cur = con.cursor()
    return con, cur


# page historique
def historique_commande_pieces(nom_fournisseur=""):
    """Requetes pour les pages d'historique des commandes"""
    conn, cur = connection_bdd()
    querry = """SELECT commande_pieces.id,date_commande,date_validation,etat,nom FROM commande_pieces
    JOIN fournisseur ON fournisseur.id=commande_pieces.idFournisseur"""
    if nom_fournisseur != "":
        querry += " WHERE fournisseur.nom='" + nom_fournisseur + "'"
    cur.execute(querry + " ORDER BY etat ASC, date_commande;")
    lignes = cur.fetchall()
    conn.close()
    return lignes


def expedition_commande(id_commande):
    """Requete pour valider l'expedition d'une commande"""
    try:
        conn, cur = connection_bdd()
        cur.execute("UPDATE commande_pieces SET etat='envoyee' WHERE id = ?", (str(id_commande)))
        conn.commit()
        conn.close()
        return True
    except lite.Error:
        return False


# page validations des receptions de commandes
def commandes_recu():
    """Requete pour renvoyer la listes des id des commandes reçues par AgiLog, non encore validée/invalidée"""
    conn, cur = connection_bdd()
    querry = """SELECT id FROM commande_pieces
    WHERE etat='envoyee';"""
    cur.execute(querry)
    lignes = cur.fetchall()
    conn.close()
    return lignes


def liste_pieces_commande(id_commande):
    """Requete pour renvoyer les pièces d'une commande définie par son id"""
    conn, cur = connection_bdd()
    querry = """SELECT designation,code_article,nombre_piece FROM pieces
    JOIN contenu_commande_pieces ON id_piece=pieces.id
    JOIN commande_pieces ON commande_pieces.id=id_commande
    WHERE commande_pieces.id=?;"""
    cur.execute(querry, (str(id_commande)))
    lignes = cur.fetchall()
    conn.close()
    return lignes


def sql_detail_commande_pieces(id_commande):
    """Permet de recupérer les données globl de la commande, ainsi qu'une table des pièces qui la constitue"""
    liste_pieces = liste_pieces_commande(id_commande)
    conn, cur = connection_bdd()
    querry = """SELECT commande_pieces.id,date_commande,date_validation,etat,nom FROM commande_pieces
    JOIN fournisseur ON fournisseur.id=commande_pieces.idFournisseur
    WHERE commande_pieces.id='{}' ;""".format(str(id_commande))
    cur.execute(querry)
    lignes = cur.fetchall()
    conn.close()
    if len(lignes) == 1:
        return lignes[0], liste_pieces
    else:
        return [], []


def change_etat_commande_recu(id_commande, etat, date_validation):
    """Requete pour valider/invalider une commande reçue par AgiLog"""
    if not (etat in ["validee", "invalidee"]):
        return False
    try:
        conn, cur = connection_bdd()
        # modification des stocks si la commande est validée
        if etat == "validee":
            liste_pieces = liste_pieces_commande(id_commande)
            for piece in liste_pieces:
                cur.execute("UPDATE pieces SET stock=stock+? WHERE code_article = ?",
                            (piece["nombre_piece"], piece["code_article"]))
        cur.execute("UPDATE commande_pieces SET etat=?,date_validation=? WHERE id = ?",
                    (etat, date_validation, str(id_commande)))
        conn.commit()
        conn.close()
        return True
    except lite.Error:
        return False


def passer_commande_pieces(dict_nombre_pieces, date_commande):
    """<dict_nombre_pieces> est un dictionnaire avec pour clé le code_article des pièces à commander,
    et comme valeur dans chaque case le nombre de pièces correspondant"""
    conn, cur = connection_bdd()
    cur.execute("SELECT id FROM fournisseur;")
    liste_id_fournisseur = cur.fetchall()
    dict_commande_par_fournisseur = {}
    for fournisseur in liste_id_fournisseur:
        dict_commande_par_fournisseur[fournisseur['id']] = {}

    cur.execute("SELECT id,code_article,idFournisseur FROM pieces;")
    liste_pieces = cur.fetchall()
    dict_idfournisseur_pieces = {}
    dict_id_pieces = {}
    for piece in liste_pieces:
        dict_id_pieces[piece['code_article']] = piece['id']
        dict_idfournisseur_pieces[piece['code_article']] = piece['idFournisseur']

    for code_article, nombre_pieces in dict_nombre_pieces.items():
        dict_commande_par_fournisseur[dict_idfournisseur_pieces[code_article]][
            dict_id_pieces[code_article]] = nombre_pieces

    for fournisseur in liste_id_fournisseur:
        if len(dict_commande_par_fournisseur[fournisseur['id']]) >= 1:
            cur.execute("INSERT INTO commande_pieces('date_commande', 'etat', 'idFournisseur') VALUES (?,?,?);",
                        (date_commande, "commandee", fournisseur['id']))
            conn.commit()
            # cur.execute("SELECT id FROM commande_pieces WHERE date_commande=? AND etat=? AND idFournisseur=?;",(date_commande, "commandee", fournisseur['id']))
            # id_commande = cur.fetchall()[0]['id']
            cur.execute("SELECT SEQ FROM SQLITE_SEQUENCE WHERE NAME='commande_pieces';")
            id_commande = cur.fetchall()[0]['SEQ']
            for id_pieces, nombre_pieces in dict_commande_par_fournisseur[fournisseur['id']].items():
                cur.execute(
                    "INSERT INTO contenu_commande_pieces('id_piece', 'id_commande', 'nombre_piece') VALUES (?,?,?)",
                    (str(id_pieces), str(id_commande), str(nombre_pieces)))
            conn.commit()
    conn.close()
    return True


# gestion stocks
def affichage_stock():
    """Fonction pour récupérer les donnes relatives à l'affichage de stock"""
    conn, cur = connection_bdd()
    querry = """SELECT pieces.id,designation,code_article,nom,stock,seuil_commande,delai,niveau_recompletion FROM pieces
        JOIN fournisseur ON fournisseur.id=pieces.idFournisseur"""
    cur.execute(querry + ";")
    lignes = cur.fetchall()
    conn.close()
    return lignes


def affichage_stock_commande(filtre=True):
    """Fonction pour récupérer les donnes relatives au passage d'une commande de pièces"""
    # table_stock_fictif est une table intermediaire qui permet de savoir le stock dans l'entrepot + les quantités en livraison pour chaque pièce
    # il faut créer une table intermedaire avec un UNION sinon elle ne contient que les pièces qui sont en commande
    filtre_querry = ""
    if filtre:
        filtre_querry = "WHERE stock_fictif<=seuil_commande"
    conn, cur = connection_bdd()
    querry = """SELECT designation,code_article,nom,stock,stock_fictif,seuil_commande,niveau_recompletion,(niveau_recompletion-stock_fictif) as commande_default FROM pieces
        JOIN fournisseur ON fournisseur.id=pieces.idFournisseur
        JOIN (SELECT id_piece,SUM(nbr_en_commande) as stock_fictif FROM(
                SELECT id_piece,nombre_piece as nbr_en_commande FROM commande_pieces
                    JOIN contenu_commande_pieces ON id_commande=id
                    WHERE etat='commandee' OR etat='envoyee'
                UNION ALL
                SELECT id,stock FROM pieces)
            GROUP BY id_piece) as table_stock_fictif
        ON table_stock_fictif.id_piece=pieces.id {} ORDER BY nom;""".format(filtre_querry)
    cur.execute(querry)
    lignes = cur.fetchall()
    conn.close()
    return lignes


def sql_init_stock(dict_pieces):
    """<dict_pieces> est un dictionnaire avec pour clé l'id des pièces',
    et comme valeur un dictionnaire des <case:valeurs>"""
    conn, cur = connection_bdd()
    print(dict_pieces)
    for id_piece, data in dict_pieces.items():
        print(id_piece)
        print(data)
        liste_case = [str(cle) for cle in data.keys()]
        query = "UPDATE pieces SET " + "=?,".join(liste_case) + "=? WHERE id = ?;"
        data_query = tuple([data[case] for case in liste_case] + [str(id_piece)])
        cur.execute(query, data_query)
    conn.commit()
    conn.close()
    return True


"""
## AGILOG

LIEN AVEC AGIGREEN/PARTS

**
Page stock initiaux

reference = SELECT id FROM pieces

UPDATE pieces SET stock=? WHERE pieces.id == ? / stock_init,reference
UPDATE pieces SET seuil_commande cmd=? WHERE pieces.id == ? / seuil,reference
UPDATE pieces SET delai cmd=? WHERE pieces.id == ? / delai,reference
UPDATE pieces SET niveau_recompletion=? WHERE pieces.id == ? / stock_CQ,reference

**
Page consultation stock

SELECT id, stock FROM pieces


LIEN AVEC AGILEAN

**
Page a expedier

commande = SELECT id FROM commande_kits

quand envoi:
UPDATE commande_kits SET etat=envoye WHERE commande_kits.id == commande






## AGILEAN ##

**
Page passer commande

SELECT nom FROM kits
"INSERT INTO contenu_commande_kit('id_kit','id_commande','nombre_kit') VALUES (?,?,?)" (id_kit,id_commande,nombre_kit)
"INSERT INTO commande_kit('id','date_commande','date_validation','etat') VALUES (?,?,?,?)" (id,date_commande,NONE,'en cours')

**
Page reception

commande = SELECT id FROM commande_kits
UPDATE commande_kits SET etat=valide WHERE commande_kits.id == commande
UPDATE commande_kits SET etat=invalide WHERE commande_kits.id == commande

UPDATE commande_kits SET date_validation=date WHERE commande_kits.id == commande



# commande={"B2*2":1,"JT":3,"P1*2":2,"P4*4":2,"P1*1":1}
# passer_commande_pieces(commande, "test")
"""
