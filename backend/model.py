"""
GA-KELM Model - Genetic Algorithm Optimized Kernel Extreme Learning Machine
Real-Time AQI Prediction System

This module implements:
1. KELM (Kernel Extreme Learning Machine) for fast regression
2. Genetic Algorithm for hyperparameter optimization
3. Combined GA-KELM for AQI prediction
"""

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.model_selection import train_test_split
import pickle
import os
import logging
from datetime import datetime

from utils import calculate_aqi_from_pm25, get_aqi_category

logger = logging.getLogger(__name__)


class KELM:
    """
    Kernel Extreme Learning Machine
    
    Uses RBF kernel for non-linear mapping and closed-form solution
    for fast training (no iterations needed).
    
    Parameters:
        C: Regularization parameter (higher = less regularization)
        gamma: RBF kernel coefficient (higher = narrower kernel)
    """
    
    def __init__(self, C=1.0, gamma=0.1):
        self.C = C
        self.gamma = gamma
        self.beta = None
        self.X_train = None
        
    def fit(self, X, y):
        """
        Train KELM using closed-form solution
        
        Formula: beta = (K + I/C)^(-1) @ y
        Where K is the RBF kernel matrix
        """
        self.X_train = X
        K = rbf_kernel(X, X, gamma=self.gamma)
        n = K.shape[0]
        
        # Regularized pseudo-inverse
        # (K + I/C)^(-1) @ y
        I = np.eye(n) / self.C
        self.beta = np.linalg.solve(K + I, y)
        
        return self
    
    def predict(self, X):
        """Make predictions on new data"""
        if self.beta is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        K = rbf_kernel(X, self.X_train, gamma=self.gamma)
        return K @ self.beta
    
    def score(self, X, y):
        """Calculate R² score"""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0


class GeneticAlgorithm:
    """
    Genetic Algorithm for KELM Hyperparameter Optimization
    
    Optimizes C and gamma parameters using evolutionary approach.
    
    Parameters:
        population_size: Number of individuals in population
        generations: Number of evolution cycles
        mutation_rate: Probability of mutation
        crossover_rate: Probability of crossover
    """
    
    def __init__(self, population_size=20, generations=30, 
                 mutation_rate=0.2, crossover_rate=0.8):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.best_params = None
        self.best_fitness = float('-inf')
        self.history = []
        
    def _initialize_population(self):
        """Create initial random population"""
        population = []
        for _ in range(self.population_size):
            # C: 0.01 to 1000 (log scale)
            # gamma: 0.001 to 10 (log scale)
            individual = {
                'C': 10 ** np.random.uniform(-2, 3),
                'gamma': 10 ** np.random.uniform(-3, 1)
            }
            population.append(individual)
        return population
    
    def _evaluate_fitness(self, individual, X_train, y_train, X_val, y_val):
        """Evaluate fitness of an individual (negative MSE)"""
        try:
            kelm = KELM(C=individual['C'], gamma=individual['gamma'])
            kelm.fit(X_train, y_train)
            y_pred = kelm.predict(X_val)
            
            # Negative MSE (we maximize fitness)
            mse = np.mean((y_val - y_pred) ** 2)
            return -mse
        except Exception:
            return float('-inf')
    
    def _tournament_selection(self, population, fitness_scores, k=3):
        """Select individual using tournament selection"""
        indices = np.random.choice(len(population), size=k, replace=False)
        best_idx = indices[np.argmax([fitness_scores[i] for i in indices])]
        return population[best_idx].copy()
    
    def _crossover(self, parent1, parent2):
        """Blend crossover (BLX-alpha)"""
        if np.random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        alpha = 0.5
        child1, child2 = {}, {}
        
        for key in ['C', 'gamma']:
            # Work in log space
            log_p1 = np.log10(parent1[key])
            log_p2 = np.log10(parent2[key])
            
            d = abs(log_p2 - log_p1)
            low = min(log_p1, log_p2) - alpha * d
            high = max(log_p1, log_p2) + alpha * d
            
            child1[key] = 10 ** np.random.uniform(low, high)
            child2[key] = 10 ** np.random.uniform(low, high)
        
        return child1, child2
    
    def _mutate(self, individual):
        """Gaussian mutation in log space"""
        mutated = individual.copy()
        
        if np.random.random() < self.mutation_rate:
            # Mutate C
            log_C = np.log10(mutated['C'])
            log_C += np.random.normal(0, 0.5)
            log_C = np.clip(log_C, -2, 3)
            mutated['C'] = 10 ** log_C
        
        if np.random.random() < self.mutation_rate:
            # Mutate gamma
            log_gamma = np.log10(mutated['gamma'])
            log_gamma += np.random.normal(0, 0.5)
            log_gamma = np.clip(log_gamma, -3, 1)
            mutated['gamma'] = 10 ** log_gamma
        
        return mutated
    
    def evolve(self, X_train, y_train, X_val, y_val, verbose=True):
        """
        Run genetic algorithm optimization
        
        Returns:
            dict: Best parameters found {'C': ..., 'gamma': ...}
        """
        population = self._initialize_population()
        
        for gen in range(self.generations):
            # Evaluate fitness
            fitness_scores = [
                self._evaluate_fitness(ind, X_train, y_train, X_val, y_val)
                for ind in population
            ]
            
            # Track best
            best_idx = np.argmax(fitness_scores)
            if fitness_scores[best_idx] > self.best_fitness:
                self.best_fitness = fitness_scores[best_idx]
                self.best_params = population[best_idx].copy()
            
            self.history.append({
                'generation': gen,
                'best_fitness': self.best_fitness,
                'best_C': self.best_params['C'],
                'best_gamma': self.best_params['gamma']
            })
            
            if verbose and gen % 5 == 0:
                logger.info("Gen %s: Best MSE=%.4f, C=%.4f, gamma=%.4f", gen, -self.best_fitness, self.best_params['C'], self.best_params['gamma'])
            
            # Create new population
            new_population = []
            
            # Elitism: keep best 2
            sorted_indices = np.argsort(fitness_scores)[::-1]
            for i in range(2):
                new_population.append(population[sorted_indices[i]].copy())
            
            # Fill rest with offspring
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                
                new_population.extend([child1, child2])
            
            population = new_population[:self.population_size]
        
        return self.best_params


class GAKELM:
    """
    GA-KELM: Genetic Algorithm Optimized Kernel ELM
    
    Combines KELM with GA for automatic hyperparameter tuning.
    """
    
    def __init__(self, population_size=20, generations=30):
        self.population_size = population_size
        self.generations = generations
        self.kelm = None
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        self.best_params = None
        self.is_trained = False
        self.training_rmse = None
        self.training_r2 = None
        self.trained_at = None
        self.data_count = 0
        
    def fit(self, X, y, verbose=True):
        """
        Train GA-KELM model
        
        1. Normalize data
        2. Split into train/validation
        3. Run GA to find optimal C and gamma
        4. Train final KELM with best parameters
        """
        if verbose:
            logger.info("Training GA-KELM Model")
        
        # Ensure y is 2D
        if len(y.shape) == 1:
            y = y.reshape(-1, 1)
        
        self.data_count = len(y)
        
        # Normalize
        X_scaled = self.scaler_X.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y)
        
        # Split
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y_scaled, test_size=0.2, random_state=42
        )
        
        # Run GA
        ga = GeneticAlgorithm(
            population_size=self.population_size,
            generations=self.generations
        )
        
        self.best_params = ga.evolve(X_train, y_train, X_val, y_val, verbose)
        
        if verbose:
            logger.info("Optimal parameters found: C=%.4f gamma=%.4f", self.best_params['C'], self.best_params['gamma'])
        
        # Train final model on all data
        self.kelm = KELM(
            C=self.best_params['C'],
            gamma=self.best_params['gamma']
        )
        self.kelm.fit(X_scaled, y_scaled)
        self.is_trained = True
        self.trained_at = datetime.now()
        
        # Calculate metrics
        y_pred = self.kelm.predict(X_scaled)
        self.training_rmse = np.sqrt(np.mean((y_scaled - y_pred) ** 2))
        
        # R² score
        ss_res = np.sum((y_scaled - y_pred) ** 2)
        ss_tot = np.sum((y_scaled - np.mean(y_scaled)) ** 2)
        self.training_r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        if verbose:
            logger.info("Training RMSE=%.4f R2=%.4f", self.training_rmse, self.training_r2)
        
        return self
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained. Call fit() first.")
        
        X_scaled = self.scaler_X.transform(X)
        y_pred_scaled = self.kelm.predict(X_scaled)
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled)
        
        return y_pred.flatten()
    
    def save(self, filepath="model.pkl"):
        """Save model to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'kelm': self.kelm,
                'scaler_X': self.scaler_X,
                'scaler_y': self.scaler_y,
                'best_params': self.best_params,
                'is_trained': self.is_trained,
                'training_rmse': self.training_rmse,
                'training_r2': self.training_r2,
                'trained_at': self.trained_at,
                'data_count': self.data_count
            }, f)
        logger.info("Model saved to %s", filepath)
    
    def load(self, filepath="model.pkl"):
        """Load model from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.kelm = data['kelm']
            self.scaler_X = data['scaler_X']
            self.scaler_y = data['scaler_y']
            self.best_params = data['best_params']
            self.is_trained = data['is_trained']
            self.training_rmse = data.get('training_rmse')
            self.training_r2 = data.get('training_r2')
            self.trained_at = data.get('trained_at')
            self.data_count = data.get('data_count', 0)
        logger.info("Model loaded from %s", filepath)
        return self


# Global model instance
_model = None
_last_trained = None

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trained_model.pkl")


def get_model():
    """Get or create model instance"""
    global _model
    if _model is None:
        _model = GAKELM(population_size=15, generations=20)
        if os.path.exists(MODEL_PATH):
            try:
                _model.load(MODEL_PATH)
            except Exception as e:
                logger.warning("Could not load model: %s", e)
                _model = GAKELM(population_size=15, generations=20)
    return _model


def train_model(data_list: list):
    """
    Train model with historical data
    
    Parameters:
        data_list: List of dicts with AQI readings
    """
    global _model, _last_trained
    
    if len(data_list) < 20:
        logger.warning("Not enough data for training (have %s, need at least 20)", len(data_list))
        return {
            "status": "error",
            "message": f"Need at least 20 records, have {len(data_list)}",
            "data_count": len(data_list)
        }
    
    # Prepare features and target
    X = []
    y = []
    
    for record in data_list:
        features = [
            record.get('pm25', 0),
            record.get('pm10', 0),
            record.get('no2', 0),
            record.get('o3', 0),
            record.get('so2', 0),
        ]
        X.append(features)
        y.append(record.get('aqi', 0))
    
    X = np.array(X)
    y = np.array(y)
    
    # Train model
    _model = GAKELM(population_size=15, generations=20)
    _model.fit(X, y, verbose=True)
    _model.save(MODEL_PATH)
    
    _last_trained = datetime.now()
    
    return {
        'status': 'success',
        'message': 'Model trained successfully',
        'C': _model.best_params['C'],
        'gamma': _model.best_params['gamma'],
        'rmse': _model.training_rmse,
        'r2': _model.training_r2,
        'data_count': len(data_list),
        'trained_at': _last_trained.isoformat()
    }


def predict_aqi(pm25=None, pm10=None, no2=None, o3=None, so2=None):
    """
    Predict AQI using trained GA-KELM model
    
    If model not trained, uses EPA formula for PM2.5 as fallback
    """
    model = get_model()
    
    # If model is trained and we have data, use the model
    if model.is_trained and pm25 is not None:
        try:
            features = np.array([[
                pm25, 
                pm10 or 0, 
                no2 or 0, 
                o3 or 0, 
                so2 or 0
            ]])
            prediction = model.predict(features)
            return round(float(prediction[0]), 2)
        except Exception as e:
            logger.warning("Model prediction error: %s; using fallback", e)
    
    # Fallback: Use EPA AQI calculation from PM2.5
    if pm25 is not None:
        return calculate_aqi_from_pm25(pm25)
    
    # If no PM2.5 provided, return None
    return None


def predict_from_data(data: dict):
    """Predict AQI from fetched data dict"""
    predicted_aqi = predict_aqi(
        pm25=data.get('pm25'),
        pm10=data.get('pm10'),
        no2=data.get('no2'),
        o3=data.get('o3'),
        so2=data.get('so2')
    )
    
    if predicted_aqi is None:
        predicted_aqi = data.get('aqi', 0)
    
    return predicted_aqi


def get_model_info():
    """Get current model status and info"""
    model = get_model()
    
    return {
        "trained": model.is_trained,
        "algorithm": "GA-KELM (Genetic Algorithm + Kernel ELM)",
        "parameters": model.best_params if model.is_trained else None,
        "rmse": model.training_rmse if model.is_trained else None,
        "r2": model.training_r2 if model.is_trained else None,
        "trained_at": model.trained_at.isoformat() if model.trained_at else None,
        "data_count": model.data_count if model.is_trained else 0,
        "model_file": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH)
    }


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing GA-KELM Model")
    
    # Generate synthetic data
    np.random.seed(42)
    X = np.random.rand(100, 5) * 100  # 5 features
    y = 0.4 * X[:, 0] + 0.3 * X[:, 1] + 0.2 * X[:, 2] + np.random.rand(100) * 10
    
    # Train
    model = GAKELM(population_size=10, generations=10)
    model.fit(X, y)
    
    # Predict
    test_X = np.random.rand(5, 5) * 100
    predictions = model.predict(test_X)
    logger.info("Predictions: %s", predictions)
