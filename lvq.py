from ucimlrepo import fetch_ucirepo
import numpy as np
from tqdm.auto import tqdm
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
import warnings
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score
)
import time
import random
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc
import collections
import numpy as np
from sklearn.model_selection import ParameterGrid
from sklearn.model_selection import cross_val_score, StratifiedKFold
from tqdm.auto import tqdm
import numpy as np

RANDOM_STATE = 51
random.seed(RANDOM_STATE)

warnings.filterwarnings('ignore')

def filter_range(min_value, max_value, X, y):
    """
    Filtra o dataset removendo linhas que possuem valores fora do range especificado
    
    Parâmetros:
    - min_value: valor mínimo aceitável
    - max_value: valor máximo aceitável  
    - X: DataFrame com as features
    - y: DataFrame/Series com o target
    
    Retorna:
    - X_filtrado: DataFrame X sem as linhas problemáticas
    - y_filtrado: DataFrame/Series y sem as linhas problemáticas
    """
    
    # Identificar linhas com valores fora do range
    linhas_problematicas = set()
    
    for feature in X.columns:
        mask_fora_range = (X[feature] < min_value) | (X[feature] > max_value)
        indices_fora_range = X[mask_fora_range].index.tolist()
        linhas_problematicas.update(indices_fora_range)
    
    linhas_problematicas = sorted(list(linhas_problematicas))
    
    # Remover linhas problemáticas
    X_filtrado = X.drop(index=linhas_problematicas)
    y_filtrado = y.drop(index=linhas_problematicas)
    
    # Calcular percentual de redução
    percentual_original = len(X)
    percentual_filtrado = len(X_filtrado)
    percentual_removido = len(linhas_problematicas)
    percentual_reducao = (percentual_removido / percentual_original) * 100
    
    print(f"📊 RESULTADO DA FILTRAGEM (Range: {min_value} - {max_value})")
    print(f"Dataset original: {percentual_original} observações")
    print(f"Dataset filtrado: {percentual_filtrado} observações")
    print(f"Linhas removidas: {percentual_removido} ({percentual_reducao:.2f}%)")
    print(f"Linhas mantidas: {100 - percentual_reducao:.2f}%")
    
    return X_filtrado, y_filtrado

eeg_eye_state = fetch_ucirepo(id=264)

X = eeg_eye_state.data.features
y = eeg_eye_state.data.targets

X, y = filter_range(3000, 6000, X, y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)



def plot_distribuicao_classes(distribuicao_classes):
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    distribuicao_classes.plot(kind='bar', color=['skyblue', 'lightcoral'])
    plt.title('Distribuição das Classes (Contagem)', fontsize=14, fontweight='bold')
    plt.xlabel('Classe')
    plt.ylabel('Número de Instâncias')
    plt.xticks([0, 1], ['Olhos Fechados (0)', 'Olhos Abertos (1)'], rotation=0)

    plt.subplot(1, 2, 2)
    plt.pie(distribuicao_classes.values, labels=['Olhos Fechados (0)', 'Olhos Abertos (1)'], 
            autopct='%1.1f%%', colors=['skyblue', 'lightcoral'])
    plt.title('Distribuição das Classes (Percentual)', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.show()

def plotar_comparacao_feature(nome_feature, X, y, X_filtrado, y_filtrado):
    """
    Cria um plot com 4 subgráficos comparando a feature antes e depois da filtragem
    
    Parâmetros:
    - nome_feature: nome da feature a ser analisada
    - X: DataFrame original
    - y: target original
    - X_filtrado: DataFrame filtrado
    - y_filtrado: target filtrado
    """
    
    # Extrair dados da feature
    dados_original = X[nome_feature]
    dados_filtrado = X_filtrado[nome_feature]
    
    # Criar figura com 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Comparação: {nome_feature} - Original vs Filtrado', fontsize=16, fontweight='bold')
    
    # 1. Boxplot Original (superior esquerdo)
    bp1 = axes[0,0].boxplot(dados_original, patch_artist=True, widths=0.6)
    bp1['boxes'][0].set_facecolor('lightcoral')
    axes[0,0].set_title('Boxplot - Dataset Original', fontsize=14, fontweight='bold')
    axes[0,0].set_ylabel('Valor')
    axes[0,0].grid(True, alpha=0.3)
    
    # Adicionar estatísticas no boxplot original
    stats_orig = f'N: {len(dados_original)}\nMédia: {dados_original.mean():.1f}\nDP: {dados_original.std():.1f}\nMin: {dados_original.min():.1f}\nMax: {dados_original.max():.1f}'
    axes[0,0].text(0.02, 0.98, stats_orig, transform=axes[0,0].transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 2. Distribuição Original (superior direito)
    axes[0,1].hist(dados_original, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
    axes[0,1].set_title('Distribuição - Dataset Original', fontsize=14, fontweight='bold')
    axes[0,1].set_xlabel('Valor')
    axes[0,1].set_ylabel('Frequência')
    axes[0,1].grid(True, alpha=0.3)
    
    # 3. Boxplot Filtrado (inferior esquerdo)
    bp2 = axes[1,0].boxplot(dados_filtrado, patch_artist=True, widths=0.6)
    bp2['boxes'][0].set_facecolor('lightblue')
    axes[1,0].set_title('Boxplot - Dataset Filtrado', fontsize=14, fontweight='bold')
    axes[1,0].set_ylabel('Valor')
    axes[1,0].grid(True, alpha=0.3)
    
    # Adicionar estatísticas no boxplot filtrado
    stats_filt = f'N: {len(dados_filtrado)}\nMédia: {dados_filtrado.mean():.1f}\nDP: {dados_filtrado.std():.1f}\nMin: {dados_filtrado.min():.1f}\nMax: {dados_filtrado.max():.1f}'
    axes[1,0].text(0.02, 0.98, stats_filt, transform=axes[1,0].transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 4. Distribuição Filtrada (inferior direito)
    axes[1,1].hist(dados_filtrado, bins=50, alpha=0.7, color='lightblue', edgecolor='black')
    axes[1,1].set_title('Distribuição - Dataset Filtrado', fontsize=14, fontweight='bold')
    axes[1,1].set_xlabel('Valor')
    axes[1,1].set_ylabel('Frequência')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Imprimir resumo comparativo
    print(f"\n📈 RESUMO COMPARATIVO - {nome_feature}")
    print(f"{'='*50}")
    print(f"{'Métrica':<20} {'Original':<12} {'Filtrado':<12} {'Melhoria':<10}")
    print(f"{'='*50}")
    print(f"{'Observações':<20} {len(dados_original):<12} {len(dados_filtrado):<12} {'-':<10}")
    print(f"{'Média':<20} {dados_original.mean():<12.2f} {dados_filtrado.mean():<12.2f} {abs(dados_original.mean() - dados_filtrado.mean()):<10.2f}")
    print(f"{'Desvio Padrão':<20} {dados_original.std():<12.2f} {dados_filtrado.std():<12.2f} {dados_original.std() - dados_filtrado.std():<10.2f}")
    print(f"{'Mínimo':<20} {dados_original.min():<12.2f} {dados_filtrado.min():<12.2f} {'-':<10}")
    print(f"{'Máximo':<20} {dados_original.max():<12.2f} {dados_filtrado.max():<12.2f} {'-':<10}")
    
    # Calcular melhoria percentual no desvio padrão
    melhoria_dp = ((dados_original.std() - dados_filtrado.std()) / dados_original.std()) * 100
    print(f"{'Melhoria DP (%)':<20} {'-':<12} {'-':<12} {melhoria_dp:<10.1f}")

def plot_param_frequencies(best_params):
    # Conta quantas vezes cada valor apareceu para cada parâmetro
    param_counts = collections.defaultdict(collections.Counter)
    
    for d in best_params:
        for k, v in d.items():
            param_counts[k][v] += 1

    # Plota individualmente para cada parâmetro, variando as cores
    for param, counter in param_counts.items():
        items = sorted(counter.items(), key=lambda x: -x[1])
        labels, values = zip(*items)
        colors = sns.color_palette("Set2", len(labels))
        plt.figure(figsize=(6, 4))
        plt.bar([str(l) for l in labels], values, color=colors)
        plt.title(f'Frequência dos valores de {param}')
        plt.ylabel('Frequência')
        plt.xlabel(param)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

def plot_stability_vs_metric(stds, means, stable_idxs, unstable_idxs, metric):
    plt.figure(figsize=(8, 5))
    plt.scatter([stds[i] for i in stable_idxs], [means[i] for i in stable_idxs], c='g', label='Mais estáveis')
    plt.scatter([stds[i] for i in unstable_idxs], [means[i] for i in unstable_idxs], c='r', label='Menos estáveis')
    plt.xlabel('Desvio padrão da métrica (estabilidade)')
    plt.ylabel(f'Média da métrica ({metric})')
    plt.title('Estabilidade x Média da Métrica (Separado)')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_metric_per_fold(scores, metric):
    plt.figure(figsize=(7, 4))
    plt.plot(range(1, 6), scores, marker='o')
    plt.title(f'{metric} em cada fold para o modelo mais estável')
    plt.xlabel('Fold')
    plt.ylabel(metric)
    plt.ylim(0, 1)
    plt.grid(True)
    plt.show()

def plot_metric_evolution(percents, train_scores, test_scores, metric):
    
    plt.figure(figsize=(8, 5))
    plt.plot(percents * 100, train_scores, label='Treino', color='b', linestyle='-')
    plt.plot(percents * 100, test_scores, label='Teste', color='r', linestyle='--')
    plt.xlabel('% do conjunto de treino utilizado')
    plt.ylabel(f'{metric.capitalize()}')
    plt.title(f'Evolução da {metric.capitalize()} no treino e teste')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_confusion_matrix(y_test, y_pred_test, model_name):
    cm = confusion_matrix(y_test, y_pred_test)
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f"Matriz de Confusão (Conjunto de Teste) - Modelo {model_name}")
    plt.xlabel('Predito')
    plt.ylabel('Real')
    plt.show()

def plot_roc_curve(model, X_test, y_test, model_name):
    if hasattr(model, "predict_proba"):
        y_score = model.predict_proba(X_test)[:, 1]
    else:
        y_score = model.decision_function(X_test)
    fpr, tpr, _ = roc_curve(y_test, y_score)
    auc_score = auc(fpr, tpr)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f'AUC = {auc_score:.3f}')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    plt.title(f'Curva ROC (Conjunto de Teste) - Modelo {model_name}')
    plt.legend()
    plt.grid(True)
    plt.show()
    return auc_score

def plot_roc_curve_evolution(model, X_test, y_test, model_name):
    if hasattr(model, "predict_proba"):
        y_score = model.predict_proba(X_test)[:, 1]
    else:
        y_score = model.decision_function(X_test)
    
    y_true = y_test.values if hasattr(y_test, 'values') else y_test
    
    n_positives = np.sum(y_true == 1)
    n_negatives = np.sum(y_true == 0)
    
    tp_cumsum = np.cumsum(y_true == 1)
    fp_cumsum = np.cumsum(y_true == 0)
    
    tpr_evolution = tp_cumsum / n_positives
    fpr_evolution = fp_cumsum / n_negatives
    
    tpr_evolution = np.concatenate([[0], tpr_evolution])
    fpr_evolution = np.concatenate([[0], fpr_evolution])
    
    plt.figure(figsize=(8, 6))
    
    colors = plt.cm.plasma(np.linspace(0, 1, len(tpr_evolution)))
    
    for i in range(1, len(tpr_evolution)):
        plt.plot([fpr_evolution[i-1], fpr_evolution[i]], 
                [tpr_evolution[i-1], tpr_evolution[i]], 
                color=colors[i], alpha=0.8, linewidth=1.5)
    
    step = max(1, len(fpr_evolution)//30)  # Mostrar ~30 pontos
    scatter = plt.scatter(fpr_evolution[::step], 
                         tpr_evolution[::step], 
                         c=range(0, len(fpr_evolution), step), 
                         cmap='plasma', s=40, alpha=0.9, 
                         edgecolors='black', linewidth=0.5)
    
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.6, label='Linha de referência')
    plt.xlabel('Taxa de Falsos Positivos (FPR)')
    plt.ylabel('Taxa de Verdadeiros Positivos (TPR)')
    plt.title(f'Evolução Temporal da Curva ROC - {model_name}')
    plt.grid(True, alpha=0.3)
    
    cbar = plt.colorbar(scatter)
    cbar.set_label('Ordem Temporal das Amostras', rotation=270, labelpad=20)
    
    plt.legend()
    plt.tight_layout()
    plt.show()
    
def plot_main_metrics(metrics_dict, model_name):
    labels = [
        "Acurácia (Treino)", "Acurácia (Teste)",
        "F1 (Treino)", "F1 (Teste)",
        "Precisão (Treino)", "Precisão (Teste)",
        "Recall (Treino)", "Recall (Teste)"
    ]
    metrics = [
        metrics_dict["accuracy_train"], metrics_dict["accuracy_test"],
        metrics_dict["f1_train"], metrics_dict["f1_test"],
        metrics_dict["precision_train"], metrics_dict["precision_test"],
        metrics_dict["recall_train"], metrics_dict["recall_test"]
    ]
    colors = sns.color_palette("Paired", 8)
    plt.figure(figsize=(8, 4))
    bars = plt.bar(range(len(metrics)), metrics, color=colors)
    plt.xticks(range(len(metrics)), labels, rotation=25, ha='right')
    plt.title(f'Métricas principais - Modelo {model_name}')
    y_min = max(min(metrics) - 0.1, 0)  # considera o menor valor de todas as métricas
    plt.ylim(y_min, 1)
    plt.tight_layout(pad=1)
    plt.show()

def search_hyperparameters(estimator, params, estm_name, metric='accuracy', n_iter=20, qnt_params=20):
    # checkpoint = load_checkpoint(estm_name)
    checkpoint = {}
    best_params = checkpoint.get('best_params', [])
    total_time = checkpoint.get('total_time', 0)
    
    for i in tqdm(range(len(best_params),qnt_params), desc="Searching Hyperparameters"):
        start_time = time.time()
        
        randomized_search = RandomizedSearchCV(
            estimator,
            param_distributions=params,
            n_iter=n_iter,
            scoring=metric,
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE + i),
            random_state=RANDOM_STATE + i,
            n_jobs=-1
        )
        randomized_search.fit(X_train, y_train)
        
        total_time += time.time() - start_time
        best_params.append(randomized_search.best_params_)
        # save_checkpoint(estm_name, {'best_params': best_params, 'total_time': total_time})
    
    plot_param_frequencies(best_params)
    print(f"Time taken for hyperparameter search: {total_time:.2f} seconds")
    return best_params


def cross_val_stability_analysis(estimator_class, param_list, metric='accuracy'):
    means = []
    stds = []
    all_scores = []
    for params in tqdm(param_list, desc="Cross-Validation for Params"):
        model = estimator_class(**params)
        scores = cross_val_score(model, X_train, y_train.values.ravel(), cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE), scoring=metric)
        means.append(np.mean(scores))
        stds.append(np.std(scores))
        all_scores.append(scores)

    # Separar modelos mais estáveis (menor desvio padrão)
    stability_threshold = np.percentile(stds, 25)
    stable_idxs = [i for i, s in enumerate(stds) if s <= stability_threshold]
    unstable_idxs = [i for i, s in enumerate(stds) if s > stability_threshold]

    # Plot separando estáveis e instáveis
    plot_stability_vs_metric(stds, means, stable_idxs, unstable_idxs, metric)

    # Selecionar o modelo mais estável com maior média da métrica
    best_idx = max(stable_idxs, key=lambda i: means[i]) if stable_idxs else np.argmax(means)
    best_params = param_list[best_idx]
    best_scores = all_scores[best_idx]

    # Plot da métrica em cada fold para o melhor modelo
    plot_metric_per_fold(best_scores, metric)

    return best_params

def evaluate_and_plot(params, model_class, metric='accuracy', model_name=None):
    
    model = model_class(**params, random_state=RANDOM_STATE) if 'random_state' in model_class().get_params() else model_class(**params)
    train_scores, test_scores = [], []
    percents = np.arange(0.2, 1.01, 0.05)
    scorer = {
        'accuracy': accuracy_score,
        'f1': f1_score,
        'precision': precision_score,
        'recall': recall_score
    }[metric]
    for p in percents:
        n = int(p * len(X_train))
        model.fit(X_train[:n], y_train[:n])
        y_pred_train = model.predict(X_train[:n])
        y_pred_test = model.predict(X_test)
        train_scores.append(scorer(y_train[:n], y_pred_train))
        test_scores.append(scorer(y_test, y_pred_test))
        
    
    plot_metric_evolution(percents, train_scores, test_scores, metric)

    # Treinamento completo
    model = model_class(**params, random_state=RANDOM_STATE) if 'random_state' in model_class().get_params() else model_class(**params)
    model.fit(X_train, y_train)
    
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    plot_confusion_matrix(y_test, y_pred_test, model_class.__name__)

    auc_score = plot_roc_curve(model, X_test, y_test, model_class.__name__)

    metrics_dict = {
        "accuracy_train": accuracy_score(y_train, y_pred_train),
        "accuracy_test": accuracy_score(y_test, y_pred_test),
        "f1_train": f1_score(y_train, y_pred_train),
        "f1_test": f1_score(y_test, y_pred_test),
        "precision_train": precision_score(y_train, y_pred_train),
        "precision_test": precision_score(y_test, y_pred_test),
        "recall_train": recall_score(y_train, y_pred_train),
        "recall_test": recall_score(y_test, y_pred_test),
        "auc": auc_score
    }
    
    if model_name is None:
        model_name = model_class.__name__
    
    plot_main_metrics(metrics_dict, model_name)

    return metrics_dict

from sklvq.models import GLVQ

glvq_param_dist = {
    'distance_type': ['squared-euclidean', 'euclidean'],
    'activation_type': ['identity', 'sigmoid', 'soft+', 'swish'],
    'solver_type': ['sgd', 'wgd', 'adam', 'lbfgs', 'bfgs'],
}

# Display the created dictionary



param_grid = ParameterGrid(glvq_param_dist)
successful_params_with_scores = []
failed_params = []

print(f"Total number of parameter combinations to test: {len(param_grid)}")

for i, params in enumerate(tqdm(param_grid, desc="Testing parameter combinations")):
    try:
        # Instantiate the GLVQ model with the current parameters
        model = GLVQ(**params, random_state=RANDOM_STATE)

        # Perform cross-validation to get a performance metric
        # Using StratifiedKFold with 5 splits as in other functions
        # Using accuracy as the scoring metric
        scores = cross_val_score(model, X_train, y_train.values.ravel(), cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE), scoring='accuracy', error_score='raise')
        mean_score = np.mean(scores)

        successful_params_with_scores.append((params, mean_score))

    except  Exception as e:
        #print(f"\nCombination {i+1}/{len(param_grid)} failed with error: {e}")
        failed_params.append((params, str(e)))
        # Continue to the next iteration even if an error occurs

print("\n--- Summary ---")
print(f"Successful parameter combinations: {len(successful_params_with_scores)}")
print(f"Failed parameter combinations: {len(failed_params)}")

# Sort the successful parameter combinations by their mean score in descending order
successful_params_with_scores.sort(key=lambda x: x[1], reverse=True)

# Select the top 20 parameter combinations
top_20_params = [params for params, score in successful_params_with_scores[:20]]

print("\nTop 20 parameter combinations based on mean cross-validation accuracy:")
for i, params in enumerate(top_20_params):
    print(f"{i+1}: {params}")

plot_param_frequencies(top_20_params)

best_params = cross_val_stability_analysis(GLVQ, top_20_params, metric='accuracy')

print("\nBest parameters after stability analysis:")
print(best_params)

metrics_dict = evaluate_and_plot(best_params, GLVQ, metric='accuracy', model_name='GLVQ')
print("\nMetrics after final evaluation:")

with open('metrics_lvq.json', 'w') as f:
    json.dump(metrics_dict, f, indent=4)

print(json.dumps(metrics_dict, indent=4))