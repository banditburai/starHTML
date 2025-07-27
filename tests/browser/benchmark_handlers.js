/**
 * Performance benchmark for StarHTML handlers
 * Measures DOM query performance, signal updates, and memory usage
 */

class HandlerBenchmark {
    constructor() {
        this.results = {};
        this.testElements = [];
    }

    /**
     * Create test DOM with many elements
     */
    setupDOM(elementCount = 1000) {
        const container = document.createElement('div');
        container.id = 'benchmark-container';
        
        // Create elements with various handlers
        for (let i = 0; i < elementCount; i++) {
            const div = document.createElement('div');
            div.id = `test-element-${i}`;
            
            // Mix of different handlers
            if (i % 3 === 0) {
                div.setAttribute('data-on-resize', `width = $el.offsetWidth`);
            }
            if (i % 5 === 0) {
                div.setAttribute('data-on-scroll', `visible = true`);
            }
            if (i % 7 === 0) {
                div.setAttribute('data-persist', 'count');
                div.setAttribute('data-signals', JSON.stringify({ count: i }));
            }
            
            container.appendChild(div);
            this.testElements.push(div);
        }
        
        document.body.appendChild(container);
    }

    /**
     * Cleanup test DOM
     */
    cleanupDOM() {
        const container = document.getElementById('benchmark-container');
        if (container) {
            container.remove();
        }
        this.testElements = [];
    }

    /**
     * Measure querySelectorAll performance
     */
    benchmarkDOMQueries() {
        const iterations = 100;
        
        // Benchmark current approach (querySelectorAll('*'))
        const startAll = performance.now();
        for (let i = 0; i < iterations; i++) {
            const allElements = document.querySelectorAll('*');
            let count = 0;
            allElements.forEach(el => {
                if (el.getAttribute('data-on-resize')) count++;
            });
        }
        const timeAll = performance.now() - startAll;
        
        // Benchmark optimized approach (specific selector)
        const startSpecific = performance.now();
        for (let i = 0; i < iterations; i++) {
            const resizeElements = document.querySelectorAll('[data-on-resize]');
            const count = resizeElements.length;
        }
        const timeSpecific = performance.now() - startSpecific;
        
        this.results.domQueries = {
            allElements: {
                time: timeAll,
                avgTime: timeAll / iterations,
                description: "querySelectorAll('*') with attribute check"
            },
            specificSelector: {
                time: timeSpecific,
                avgTime: timeSpecific / iterations,
                description: "querySelectorAll('[data-on-resize]')"
            },
            improvement: ((timeAll - timeSpecific) / timeAll * 100).toFixed(2) + '%'
        };
    }

    /**
     * Measure signal update performance
     */
    benchmarkSignalUpdates() {
        // Setup mock signal system
        window.$ = {};
        const iterations = 1000;
        const signals = 50;
        
        // Create signal patch
        const signalPatch = {};
        for (let i = 0; i < signals; i++) {
            signalPatch[`signal_${i}`] = Math.random();
        }
        
        // Benchmark current approach
        const startCurrent = performance.now();
        for (let i = 0; i < iterations; i++) {
            if (window.$ && typeof window.$ === 'object') {
                Object.keys(signalPatch).forEach(key => {
                    if (window.$[key] !== signalPatch[key]) {
                        window.$[key] = signalPatch[key];
                    }
                });
                document.dispatchEvent(new CustomEvent('datastar-signal-patch', {
                    detail: signalPatch,
                    bubbles: true
                }));
            }
        }
        const timeCurrent = performance.now() - startCurrent;
        
        // Benchmark optimized approach (Object.assign)
        const startOptimized = performance.now();
        for (let i = 0; i < iterations; i++) {
            if (window.$?.constructor === Object) {
                Object.assign(window.$, signalPatch);
                document.dispatchEvent(new CustomEvent('datastar-signal-patch', {
                    detail: signalPatch,
                    bubbles: true
                }));
            }
        }
        const timeOptimized = performance.now() - startOptimized;
        
        this.results.signalUpdates = {
            current: {
                time: timeCurrent,
                avgTime: timeCurrent / iterations,
                description: "Individual key updates with checks"
            },
            optimized: {
                time: timeOptimized,
                avgTime: timeOptimized / iterations,
                description: "Object.assign batch update"
            },
            improvement: ((timeCurrent - timeOptimized) / timeCurrent * 100).toFixed(2) + '%'
        };
    }

    /**
     * Measure expression execution performance
     */
    benchmarkExpressionExecution() {
        const iterations = 1000;
        const expressions = [
            'width = 100',
            'height = $el.offsetHeight',
            'visible = scrollY > 100',
            'active = width > 768 && height > 400'
        ];
        
        // Benchmark new Function approach
        const startNewFunction = performance.now();
        for (let i = 0; i < iterations; i++) {
            expressions.forEach(expr => {
                try {
                    const fn = new Function('$el', 'width', 'height', 'scrollY', expr);
                    fn.call({}, {}, 100, 200, 300);
                } catch (e) {}
            });
        }
        const timeNewFunction = performance.now() - startNewFunction;
        
        // Benchmark safe evaluator approach (simulated)
        const startSafeEval = performance.now();
        for (let i = 0; i < iterations; i++) {
            expressions.forEach(expr => {
                try {
                    // Simulate parsing and safe evaluation overhead
                    const tokens = expr.split(/\s+/);
                    const result = tokens.length > 0;
                } catch (e) {}
            });
        }
        const timeSafeEval = performance.now() - startSafeEval;
        
        this.results.expressions = {
            newFunction: {
                time: timeNewFunction,
                avgTime: timeNewFunction / (iterations * expressions.length),
                description: "new Function() dynamic execution"
            },
            safeEvaluator: {
                time: timeSafeEval,
                avgTime: timeSafeEval / (iterations * expressions.length),
                description: "Safe expression evaluator (simulated)"
            },
            overhead: ((timeSafeEval - timeNewFunction) / timeNewFunction * 100).toFixed(2) + '%'
        };
    }

    /**
     * Measure memory usage
     */
    async measureMemoryUsage() {
        if (performance.memory) {
            const before = performance.memory.usedJSHeapSize;
            
            // Create many handler instances
            const handlers = [];
            for (let i = 0; i < 100; i++) {
                const handler = {
                    elements: new WeakMap(),
                    activeElements: new Set(),
                    config: { throttle: 100, expression: 'test' }
                };
                handlers.push(handler);
            }
            
            // Force garbage collection if available
            if (window.gc) {
                window.gc();
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            const after = performance.memory.usedJSHeapSize;
            
            this.results.memory = {
                before: before,
                after: after,
                difference: after - before,
                differenceKB: ((after - before) / 1024).toFixed(2) + ' KB'
            };
        } else {
            this.results.memory = {
                error: 'performance.memory not available'
            };
        }
    }

    /**
     * Run all benchmarks
     */
    async runAll(elementCount = 1000) {
        console.log(`Starting benchmark with ${elementCount} elements...`);
        
        this.setupDOM(elementCount);
        
        console.log('Running DOM query benchmark...');
        this.benchmarkDOMQueries();
        
        console.log('Running signal update benchmark...');
        this.benchmarkSignalUpdates();
        
        console.log('Running expression execution benchmark...');
        this.benchmarkExpressionExecution();
        
        console.log('Measuring memory usage...');
        await this.measureMemoryUsage();
        
        this.cleanupDOM();
        
        return this.results;
    }

    /**
     * Display results
     */
    displayResults() {
        console.log('\n=== Benchmark Results ===\n');
        
        console.log('DOM Queries:');
        console.table(this.results.domQueries);
        
        console.log('\nSignal Updates:');
        console.table(this.results.signalUpdates);
        
        console.log('\nExpression Execution:');
        console.table(this.results.expressions);
        
        if (this.results.memory) {
            console.log('\nMemory Usage:');
            console.table(this.results.memory);
        }
        
        return this.results;
    }
}

// Export for use in tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HandlerBenchmark;
}