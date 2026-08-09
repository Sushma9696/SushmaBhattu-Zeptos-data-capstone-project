### Executive Data Story & EDA Insights

### 1. Missing Value Strategy 

deck (77.10% Missing): Dropped entirely because missingness exceeds the 30% threshold. Imputing over three-quarters of a feature distorts feature distributions. 
 
age (19.87% Missing): Imputed using conditional medians based on pclass and sex groups (within the 5%–30% threshold). 
 
embarked / embark_town (0.22% Missing): Below the 5% threshold; dropped the 2 affected rows. 
 
### 2. Outliers & Skewness Analysis 
 
Outliers (IQR Rule): 
age: 42 outliers (>57.0 years). 
fare: 116 outliers (>65.65). 
 
Fare Distribution Skewness: 
Mean: $32.20 | Median: $14.45 | Mode: $8.05 
Ordering: Mean > Median > Mode. This confirms a heavily right-skewed (positively skewed) distribution dominated by lower fares with a long upper tail of premium tickets. 
 
### 3. Bivariate & Off-Diagonal Correlations 
 
Survival Rates:Sex:  
Female = 74.20%, Male = 18.89% 
Pclass: 1st = 62.96%, 2nd = 47.28%, 3rd = 24.24% 
Sex x Pclass: 1st Class Female = 96.81% vs. 3rd Class Male = 13.54% 
 
Top 2 Off-Diagonal Correlations: 
pclass - fare (r = -0.5495, |r| = 0.5495): Inverse relation reflecting higher numerical class values (3rd Class) commanding lower ticket prices. 
sibsp - parch (r = +0.4148, |r| = 0.4148): Positive correlation showing passengers traveling with siblings/spouses frequently traveled with parents/children. 

### 4. Multivariate Data Story Interpretations

Chart 1 (Survival by Class & Sex): Demonstrates the combined effect of demographic policies ("women and children first") and socioeconomic privilege. 1st class women survived at 96.81%, whereas 3rd class men suffered an 86.46% mortality rate.

Chart 2 (Fare Distribution across Classes by Survival): Shows that across all three ticket classes, surviving passengers systematically possessed higher median and upper-quartile fare values, proving cabin location and proximity to lifeboats favored higher-paying passengers.

Chart 3 (Age Split across Classes & Survival): Reveals an age survival advantage in 2nd and 3rd classes for children under 10 years old, whereas working-age adults in 3rd class experienced high mortality.

Chart 4 (Age vs. Fare Interactions): Indicates that mortality is heavily concentrated in the low-fare (<$30), young-adult age range (20–40 years). Paying a fare above $100 served as a strong predictor of survival regardless of age.

### Predictive Modeling & Imbalance Evaluations

Stratified Split Justification

The target variable survived exhibits an asymmetric distribution (~38.4% survived vs. ~61.6% died). Applying a stratified split guarantees that both training and testing folds retain the exact 38.4 / 61.6 class balance, preventing distribution drift during training and evaluation.

### Imbalance Handling Comparison

Baseline (No Handling): Precision = 0.7969, Recall = 0.7391, F1 = 0.7669

class_weight='balanced': Precision = 0.7846, Recall = 0.7391, F1 = 0.7612

SMOTE (Train fold only): Precision = 0.7432, Recall = 0.7971, F1 = 0.7692

Conclusion: SMOTE applied to the training fold achieved the best overall F1 score (0.7692) and highest recall (0.7971). While baseline precision was slightly higher, SMOTE effectively reduced false negatives, which is critical in survival prediction scenarios.

Hyperparameter Tuning & Regression Side-Task Conclusions

GridSearchCV Best Parameters: 
{'classifier__max_depth': 6, 'classifier__max_features': 'sqrt', 'classifier__n_estimators': 100}

Out-of-Bag (OOB) Score: 0.8143

Heteroscedasticity Analysis: The linear regression residual plot for fare prediction displays strong heteroscedasticity (a funnel/fan pattern where residual spread expands significantly as predicted fare increases). This occurs because low fares cluster tightly around $8-$30, while premium fares vary widely up to $500+.


### Final Deployment Recommendation

I recommend deploying the Tuned Random Forest Classifier (titanic_pipeline.joblib).

This model achieves the highest overall accuracy (83.15%), ROC AUC (0.8679), and F1 Score (0.7756), striking an optimal balance between precision (81.54%) and recall (73.91%). Unlike individual decision trees, which overfit to high-variance features like fare, the ensemble architecture generalizes well across edge cases while maintaining an Out-of-Bag validation score of 81.43%. Embedded within a scikit-learn Pipeline alongside a ColumnTransformer, the model safely handles unseen missing values and categorical transformations at inference time without risk of data leakage.