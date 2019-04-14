# -*- coding: utf-8 -*-
"""
Created on Mon Aug  6 19:29:59 2018

@author: amoat
"""

from flask import Flask, request, render_template, send_file
from werkzeug import secure_filename





app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/overlaps')
def overlaps():
    return render_template('overlaps.html')

@app.route('/overlaps', methods=['POST'])
def overlaps_form_post():
    temp_var = request.form['testcol']
    return '<p>' + temp_var + 'eshta8al </p>'

@app.route('/ngrams')
def ngrams():
    return render_template('ngrams.html')

@app.route('/ngrams', methods=['POST'])
def ngrams_form_post():
    from nltk import ngrams
    from nltk import FreqDist
    from io import BytesIO
    import pandas as pd
    import re
    import operator
    import os
    
    english_stopwords = pd.read_csv('english_stopwords.txt', encoding='UTF-8',names=['words'])
    english_stopwords = list(english_stopwords['words'])
    arabic_stopwords = pd.read_csv('arabic_stopwords.txt', encoding='UTF-8', names=['words'])
    arabic_stopwords = list(arabic_stopwords['words'])
    
    def replaceMultiple(mainString, toBeReplaces, newString):
        # Iterate over the strings to be replaced
        for elem in toBeReplaces :
            # Check if string is in the main string
            if elem in mainString :
                # Replace the string
                mainString = mainString.replace(elem, newString)
        
        return  mainString

    def remove_stop_words(text):
    #print(text)
        filtered_word_list = [] #make a copy of the word_list
        for word in text.split(): # iterate over word_list
            if((word not in english_stopwords) and (word not in arabic_stopwords)):
                filtered_word_list.append(word)# remove word from filtered_word_list if it is a stopword
                
        return filtered_word_list


    file = request.files['file']
    text_col = request.form['column']
    try:
        uni = request.form['unigrams']
    except:
        uni='off'
    try:
        bi = request.form['bigrams']
    except:
        bi='off'
    try:
        tri = request.form['trigrams']
    except:
        tri = 'off'
        
    
    file.save(secure_filename(file.filename))
    
    if(file.filename.split('.')[-1] == 'xlsx'):
        df = pd.read_excel(file.filename)
    else:
        df = pd.read_csv(file.filename, encoding='UTF-8')
    
    snippets = df[text_col].astype(str)
    
    snippets = [x.replace('’', "'") for x in snippets]
    snippets = [' '.join(remove_stop_words(x)) for x in snippets]
    snippets_clean = []
    
    for s in snippets: 
        t = s
        
        # remove numbers
        t = ''.join([i for i in t if not i.isdigit()])
        
        #remove hashtags
        t = re.sub(r"(?:@\S*|#\S*|http(?=.*://)\S*|pic.twitter\S*|RT(?=.*@)\S*)", "", t)
        
        '''
        Replace multiple characters / strings from a string
        '''
        
        
        # Replace all the occurrences of string in list by AA in the main list 
        otherStr = replaceMultiple(t.lower(), [':', '.',',', '?', ',', '،', '؛', '‘', '’', '`', '~', '?', '؟', '-', ';', 'ـ', '#', '_'] , " ")
        otherStr = replaceMultiple(otherStr, ['ّ', 'َ', 'ً', 'ُ', 'ٌ', 'ِ', 'ٍ', 'ْ'], "")
        otherStr = replaceMultiple(otherStr, ['أ', 'آ', 'إ'], 'ا')
        otherStr = replaceMultiple(otherStr, ['ى'], "ي")
        otherStr = replaceMultiple(otherStr, ['ة'], 'ه')
        otherStr = replaceMultiple(otherStr, ['(', ')', '{', '}', '[', ']', '<', '>', '<', '>', 'ـ', '{','}','–', '.', ':',','], '')
        #remove words with less than 2 characters
        
        
        final_words = []
        for w in otherStr.split():
            if(len(w) > 2):
                final_words.append(w)
        
        otherStr = ' '.join(final_words)
        
        snippets_clean.append(otherStr.strip())

#    print(snippets_clean[0], file=sys.stdout)
#
#
    words=[]
    bigrams=[]
    trigrams=[]
   
    if(uni == 'option1'):
        snippets_1 = [ngrams(x.split(), 1) for x in snippets_clean]
        snippets_1_filtered = [list(x) for x in snippets_1]
        for s in snippets_1_filtered:
            words.append([' '.join(x) for x in s])

    if(bi == 'option1'):
        snippets_2 = [ngrams(x.split(), 2) for x in snippets_clean]
        snippets_2_filtered = []
        for s in range(0, len(snippets_2)):
            try:
                snippets_2_filtered.append(list(snippets_2[s]))
            except:
                continue
        for s in snippets_2_filtered:
            bigrams.append([' '.join(x) for x in s])
   
    if(tri == 'option1'):
        snippets_3 = [ngrams(x.split(), 3) for x in snippets_clean]
        snippets_3_filtered = []
        for s in range(0, len(snippets_3)):
            try:
                snippets_3_filtered.append(list(snippets_3[s]))
            except:
                continue
        for s in snippets_3_filtered:
            trigrams.append([' '.join(x) for x in s])   
  

    full_list = words + bigrams + trigrams
    flat_list = [item for sublist in full_list for item in sublist]
#    
#    print(flat_list[:10], file=sys.stdout)
#
    ngrams = dict(FreqDist(flat_list))
    sorted_ngrams = sorted(ngrams.items(), key=operator.itemgetter(1),reverse=True)    
    os.remove(file.filename)
 
#    
#    print(pd.Series(dict(sorted_ngrams[:100])), file=sys.stdout)
#    
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    pd.Series(dict(sorted_ngrams[:1000])).to_excel(writer, sheet_name='Sheet1', header=False)
    writer.save()
    output.seek(0)
    #return '<p>'+uni+bi+tri+'</p>'
    return send_file(output, attachment_filename=request.form['output_file']+'.xlsx', as_attachment=True)
