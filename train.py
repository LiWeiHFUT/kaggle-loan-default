import numpy as np
import time
from sklearn import linear_model
from sklearn.externals import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.cross_validation import ShuffleSplit
from sklearn.svm import SVR
from sklearn.metrics import f1_score, roc_auc_score

def main():
    xtrain=np.load('data/x_train.npy')
    ytrain=np.load('data/y_train.npy')
    ytrainreg=np.load('data/loss.npy')
    
    #train-test split
    ss1=ShuffleSplit(np.shape(ytrain)[0],n_iter=1, test_size=0.2, random_state=42)
    for train_idx, test_idx in ss1:
        xtest=xtrain[test_idx,:]
        ytest=ytrain[test_idx]
        ytestreg=ytrainreg[test_idx]
        xtrain=xtrain[train_idx,:]
        ytrain=ytrain[train_idx]
        ytrainreg=ytrainreg[train_idx]
    
    #regression data
    xtrain_reg=xtrain[ytrainreg>0]
    loss_reg=ytrainreg[ytrainreg>0]
    
    #split regression training data into train set and cross-validation set (for ensembling)
    ss2=ShuffleSplit(np.shape(loss_reg)[0],n_iter=1,test_size=0.3, random_state=42)
    for train_idx, test_idx in ss2:
        xcv=xtrain_reg[test_idx,:]
        loss_cv=loss_reg[test_idx]
        xtrain_reg=xtrain_reg[train_idx,:]
        loss_reg=loss_reg[train_idx]
        
        
    #classification features, generated by clf_selector.py
    sel_clf_feats=np.load('features/clf_sel.npy')
    
    #regression features
    #generated by reg_selector_sgd_eps_log.py
    sel_reg1=np.load('features/reg_sel_sgd_eps.npy')
    #generated by reg_selector_quant_log.py
    sel_reg2=np.load('features/reg_sel_quant.npy')
    #generated by reg_selector_lad_log.py
    sel_reg3=np.load('features/reg_sel_lad.npy') 
    
    feats_mat=np.vstack((sel_reg1,sel_reg2,sel_reg3))
    regs_unique=5
    feat_indic=np.hstack((0*np.ones(regs_unique),1*np.ones(regs_unique),
                          2*np.ones(regs_unique))) #maps regressors to features
    
    clf=GradientBoostingClassifier(init=None, learning_rate=0.1, loss='deviance',
                  max_depth=5, max_features='auto', min_samples_leaf=1,
                  min_samples_split=2, n_estimators=500, random_state=42,
                  subsample=1.0, verbose=0)
    
    t0=time.time()
    print "fitting classifier"
    clf.fit(xtrain[:,sel_clf_feats],ytrain)
    print "done with classifier"
    print "time taken", time.time()-t0
    joblib.dump(clf,'models/clf.pkl',compress=3)
    
    reg1=linear_model.SGDRegressor(loss='epsilon_insensitive',random_state=0,n_iter=100)
    reg6=linear_model.SGDRegressor(loss='epsilon_insensitive',random_state=0,n_iter=100)
    reg11=linear_model.SGDRegressor(loss='epsilon_insensitive',random_state=0,n_iter=100)
    reg2=SVR(C=0.01,kernel='linear',random_state=42)
    reg7=SVR(C=0.01,kernel='linear',random_state=42)
    reg12=SVR(C=0.01,kernel='linear',random_state=42)
    reg3=GradientBoostingRegressor(loss='lad',min_samples_leaf=5,
                                   n_estimators=1000,random_state=42)
    reg8=GradientBoostingRegressor(loss='lad',min_samples_leaf=5,
                                    n_estimators=1000,random_state=42)
    reg13=GradientBoostingRegressor(loss='lad',min_samples_leaf=5,
                                    n_estimators=1000,random_state=42)
    reg4=GradientBoostingRegressor(loss='huber',alpha=0.6, min_samples_leaf=5,
                                    n_estimators=1000,random_state=42)
    reg9=GradientBoostingRegressor(loss='huber',alpha=0.6, min_samples_leaf=5,
                                    n_estimators=1000, random_state=42)
    reg14=GradientBoostingRegressor(loss='huber',alpha=0.6, min_samples_leaf=5,
                                    n_estimators=500, random_state=42)
    reg5=GradientBoostingRegressor(loss='quantile',alpha=0.45, min_samples_leaf=5,
                                    n_estimators=1000,random_state=42)
    reg10=GradientBoostingRegressor(loss='quantile',alpha=0.45,min_samples_leaf=5,
                                    n_estimators=1000,random_state=42)
    reg15=GradientBoostingRegressor(loss='quantile',alpha=0.45,min_samples_leaf=5,
                                    n_estimators=1000,random_state=42)                               
    
    #gather base regressors
    regs=[reg1,reg2,reg3,reg4,reg5,reg6,reg7,reg8,reg9,reg10,reg11,reg12,
          reg13,reg14,reg15]
    n_regs=len(regs)
    
    print "fitting regressors"
    j=0
    i=1
    for reg in regs:
        feats=feats_mat[(feat_indic[j]),:]
        t0=time.time()
        print "fitting",i, "no of features", np.sum(feats)
        reg.fit(xtrain_reg[:,feats],np.log(loss_reg)) #training on the log of the loss
        print "done with",i
        print "time taken", time.time()-t0
        joblib.dump(reg,'models/reg%s.pkl' % str(i),compress=3)
        i+=1
        j+=1
    
    reg_ens1=linear_model.SGDRegressor(loss='huber',random_state=0,n_iter=100)
    reg_ens2=linear_model.SGDRegressor(loss='epsilon_insensitive',random_state=0,n_iter=100)
    reg_ens3=SVR(C=0.01,kernel='linear',random_state=42)
    reg_ens4=GradientBoostingRegressor(loss='huber',alpha=0.6, min_samples_leaf=5,
                                    n_estimators=1000, random_state=42)
    reg_ens5=GradientBoostingRegressor(loss='lad',n_estimators=1000,min_samples_leaf=5,
                                       random_state=42)
    reg_ens6=GradientBoostingRegressor(loss='quantile',alpha=0.45, min_samples_leaf=5,
                                    n_estimators=1000,random_state=42)
    
    #gather ensemblers
    reg_ens=[reg_ens1,reg_ens2,reg_ens3,reg_ens4,reg_ens5,reg_ens6]
    n_reg_ens=len(reg_ens) 
    
    rows_cv=np.shape(xcv)[0]
    cv_mat=np.zeros((rows_cv,n_regs)) #matrix of base predictions for ensemblers
    
    
    print "predicting regression values for CV"
    j=0
    i=1
    for reg in regs:
        feats=feats_mat[(feat_indic[j]),:]
        print "predicting for reg",i, "no of features", np.sum(feats) 
        tmp_preds=reg.predict(xcv[:,feats])
        tmp_preds=np.exp(tmp_preds) #training was done on log of loss, hence the exp
        tmp_preds=np.abs(tmp_preds)
        tmp_preds[tmp_preds>100]=100
        cv_mat[:,j]=tmp_preds
        j+=1
        i+=1
    
    print "fitting ensemble regressors"
    
    i=1
    for reg in reg_ens:
        print "fitting",i
        reg.fit(cv_mat,loss_cv) #for the ensemblers, training was done on the regular loss
        joblib.dump(reg,'models/reg_ens%s.pkl' % str(i),compress=3)
        i+=1
    
    rows_test=np.shape(xtest)[0]
    test_mat=np.zeros((rows_test,n_regs)) #matrix for base predictions on test set
    
    print "test-set predicting"
    class_preds=clf.predict(xtest[:,sel_clf_feats])
    
    print "predicting regression values for test set"
    j=0
    i=1
    for reg in regs:
        feats=feats_mat[(feat_indic[j]),:]
        print "predicting for reg",i
        tmp_preds=reg.predict(xtest[:,feats])
        tmp_preds=np.exp(tmp_preds) #training was done on log of loss, hence the exp
        tmp_preds=np.abs(tmp_preds)
        tmp_preds[tmp_preds>100]=100    
        test_mat[:,j]=tmp_preds
        j+=1
        i+=1
    
    ens_mat=np.zeros((rows_test,n_reg_ens)) #matrix for ensemble predictions
    j=0
    i=1
    print "predicting ensembles"
    for reg in reg_ens:
        print "predicting for reg_ens",i
        tmp_preds=reg.predict(test_mat)
        tmp_preds=np.abs(tmp_preds)
        tmp_preds[tmp_preds>100]=100
        ens_mat[:,j]=tmp_preds
        j+=1
        i+=1
    
    #multiply regression predictions with class predictions
    loss_mat=np.multiply(test_mat,class_preds[:,np.newaxis])
    #multiply regression predictions with correct classes for mae benchmarks
    correct_loss=np.multiply(test_mat,ytest[:,np.newaxis])
    
    #multiply ensemble predictions with class predictions    
    ens_losses=np.multiply(ens_mat,class_preds[:,np.newaxis])
    #multiply ensemble predictions with correct classes for mae benchmarks
    ens_losses_correct=np.multiply(ens_mat,ytest[:,np.newaxis])
    
    print "predictor performance"
    print "output format:"
    print "model","\t", "mae","\t", "mae for correct classes","\t", "mae for defaults"
    print "individual learners"
    for k in range(n_regs):
        tmp_preds=loss_mat[:,k]
        mae1=np.mean(np.abs(tmp_preds-ytestreg))
        tmp_preds2=correct_loss[:,k]
        mae2=np.mean(np.abs(tmp_preds2-ytestreg))
        mae3=np.mean(np.abs(tmp_preds2[tmp_preds2>0]-ytestreg[tmp_preds2>0]))
        print "reg",k+1,"\t",mae1,"\t",mae2,"\t",mae3
    
    print "ensemblers"
    for k in range(n_reg_ens):
        tmp_preds=ens_losses[:,k]
        mae1=np.mean(np.abs(tmp_preds-ytestreg))
        tmp_preds2=ens_losses_correct[:,k]
        mae2=np.mean(np.abs(tmp_preds2-ytestreg))  
        mae3=np.mean(np.abs(tmp_preds2[tmp_preds2>0]-ytestreg[tmp_preds2>0]))
        print "reg_ens",k+1,"\t",mae1,"\t",mae2,"\t",mae3
    
    #mean of all ensemblers
    mean_ens_losses=np.mean(ens_losses,1)
    mean_ens_correct=np.mean(ens_losses_correct,1)
    mae1=np.mean(np.abs(mean_ens_losses-ytestreg))
    mae2=np.mean(np.abs(mean_ens_correct-ytestreg))
    mae3=np.mean(np.abs(mean_ens_correct[mean_ens_correct>0]-ytestreg[mean_ens_correct>0]))
    print "mean_ens","\t",mae1,"\t",mae2,"\t",mae3
    
    #mean of two best ensemblers
    best_ens=np.mean(ens_losses[:,(0,2)],1)
    best_ens_correct=np.mean(ens_losses_correct[:,(0,2)],1)
    mae1=np.mean(np.abs(best_ens-ytestreg))
    mae2=np.mean(np.abs(best_ens_correct-ytestreg))
    mae3=np.mean(np.abs(best_ens_correct[best_ens_correct>0]-ytestreg[best_ens_correct>0]))
    print "best_ens","\t",mae1,"\t",mae2,"\t",mae3
    
    #other benchmarks
    print "mae for class_preds:"
    print np.mean(np.abs(class_preds-ytestreg))
    print "mae for 3*class_preds:"
    print np.mean(np.abs(3*class_preds-ytestreg))
    print "roc_auc for classes:"
    print roc_auc_score(ytest,class_preds)
    print "f1-score for classes:"
    print f1_score(ytest,class_preds)
    print "mae of all zeroes"
    print np.mean(np.abs(0-ytestreg))

if __name__=="__main__":
    main()