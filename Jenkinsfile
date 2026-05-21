pipeline {
    agent any
    
    stages {        
        stage('QA') {
            parallel {
                stage('Code style') {
                    steps {
                        sh """
                            # Install pycodestyle if missing (user space)
                            python3 -m pip install --user pycodestyle || true
                            python3 -m pycodestyle hr_time || true
                        """
                    }
                }
                stage('Unit Tests (CI)') {
                    steps {
                        sh '''
                            echo "Running pure unit tests (no Frappe dependencies)..."
                            # Use explicit directory discovery
                            python3 -m unittest discover -s hr_time/tests/unit -p "test_*.py" -v

                            echo "Frappe integration tests require bench environment and are excluded from CI."
                        '''
                    }
                }
            }
        }
    }
}