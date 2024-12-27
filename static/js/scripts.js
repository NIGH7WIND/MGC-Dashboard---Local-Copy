function analyzeSentiment() {
    resetContent();

    // Clear existing chart and show loading animation
    Plotly.purge('chart-display');
    Plotly.purge('pie-chart');

    const companyName = document.getElementById('company-name').value.trim();
    const timePeriod = document.getElementById('time-period').value;

    updateLoader();

    // analyzing animation
    const analyzeButton = document.querySelector('.analyze-btn');
    analyzeButton.innerText = 'Analyzing...';
    analyzeButton.classList.add('analyzing');
    analyzeButton.disabled = true;

    // Show loading animation
    document.getElementById('loading').style.display = 'block';
    document.getElementById('gauge-loading').style.display = 'block';

    // Update the company name and Date
    document.getElementById('today-date').textContent = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
    document.getElementById('company-name-display').textContent = companyName;
    document.getElementById('date-range').textContent = document.getElementById('time-period').selectedOptions[0].textContent;

    fetch('/scraper-score', {
        method: 'POST',
        body: JSON.stringify({ companyName, timePeriod }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(response => {
        const companyName = response.companyName;
        const sentimentData = JSON.parse(response.data);

        // Reset the analysebutton style
        analyzeButton.innerText = 'Analyze Sentiment';
        analyzeButton.classList.remove('analyzing');
        analyzeButton.disabled = false;


        // Enable the "Generate Report" button once the sentiment data is received
        const generateReportButton = document.querySelector('.generate-btn');
        generateReportButton.disabled = false;
        generateReportButton.style.display = 'block';
        generateReportButton.onclick = function() {
            generateReport(companyName, sentimentData);
        };

        // Find the highest positive_sentiment and highest negative_sentiment along with their corresponding date
        const highestPositive = sentimentData.reduce((max, current) => max.positive_sentiment > current.positive_sentiment ? max : current);
        const highestNegative = sentimentData.reduce((max, current) => max.negative_sentiment > current.negative_sentiment ? max : current);

        // Update the Negative Score and Postive score with dates
        document.getElementById('Best_score').textContent = highestPositive.positive_sentiment + "%";
        document.getElementById('Worst_score').textContent = highestNegative.negative_sentiment + "%";
        document.getElementById('Best_score_date').textContent = highestPositive.date;
        document.getElementById('Worst_score_date').textContent = highestNegative.date;

        // Add click event listener to Best_score_date
        document.getElementById('Best_score_date').addEventListener('click', () => {
            const date = highestPositive.date;
            const sentimentDataForDate = sentimentData.filter(d => d.date === date);
            const articleHeadings = sentimentDataForDate.map(d => d.headline);
            const articleLinks = sentimentDataForDate.map(d => d.link);
            const positiveScores = sentimentDataForDate.map(d => d.positive_sentiment);
            const negativeScores = sentimentDataForDate.map(d => d.negative_sentiment);

            const positiveLinks = [];
            for (let i = 0; i < articleHeadings.length; i++) {
                if (positiveScores[i] > negativeScores[i]) {
                    positiveLinks.push(`<li><a href="${articleLinks[i]}" target="_blank">${articleHeadings[i]}</a></li>`);
                }
            }

            document.getElementById('positive_links').innerHTML = `
                <h3>Positive Articles</h3>
                <ul>${positiveLinks.join('')}</ul>
            `;
        });

        // Add click event listener to Worst_score_date
        document.getElementById('Worst_score_date').addEventListener('click', () => {
            const date = highestNegative.date;
            const sentimentDataForDate = sentimentData.filter(d => d.date === date);
            const articleHeadings = sentimentDataForDate.map(d => d.headline);
            const articleLinks = sentimentDataForDate.map(d => d.link);
            const positiveScores = sentimentDataForDate.map(d => d.positive_sentiment);
            const negativeScores = sentimentDataForDate.map(d => d.negative_sentiment);

            const negativeLinks = [];
            for (let i = 0; i < articleHeadings.length; i++) {
                if (negativeScores[i] > positiveScores[i]) {
                    negativeLinks.push(`<li><a href="${articleLinks[i]}" target="_blank">${articleHeadings[i]}</a></li>`);
                }
            }

            document.getElementById('negative_links').innerHTML = `
                <h3>Negative Articles</h3>
                <ul>${negativeLinks.join('')}</ul>
            `;
        });

        // Aggregate data by date
        const aggregatedData = d3.rollup(
            sentimentData,
            v => ({
                positive_sentiment: d3.mean(v, d => d.positive_sentiment).toFixed(0),
                negative_sentiment: d3.mean(v, d => d.negative_sentiment).toFixed(0),
                neutral_sentiment: d3.mean(v, d => d.neutral_sentiment).toFixed(0),
            }),
            d => d.date
        );

        // Convert to array and sort by date
        const data = Array.from(aggregatedData, ([date, scores]) => ({
            date: date,
            positive_sentiment: parseFloat(scores.positive_sentiment), // Convert back to numbers if needed
            negative_sentiment: parseFloat(scores.negative_sentiment),
            neutral_sentiment: parseFloat(scores.neutral_sentiment),
        }))
        .sort((a, b) => new Date(a.date) - new Date(b.date));


        // Set up initial Plotly data with y-values set to 0
        const initialTracePositive = {
            x: data.map(d => d.date),
            y: data.map(d => 0),
            type: 'bar',
            name: 'Positive',
            marker: { color: 'steelblue' }
        };

        const initialTraceNegative = {
            x: data.map(d => d.date),
            y: data.map(d => 0),
            type: 'bar',
            name: 'Negative',
            marker: { color: 'red' }
        };

        // Set up final Plotly data with actual y-values
        const finalTracePositive = {
            x: data.map(d => d.date),
            y: data.map(d => d.positive_sentiment),
            type: 'bar',
            name: 'Positive',
            marker: { color: 'steelblue' },
        };

        const finalTraceNegative = {
            x: data.map(d => d.date),
            y: data.map(d => -d.negative_sentiment), // Invert negative score for plotting below x-axis
            type: 'bar',
            name: 'Negative',
            marker: { color: 'red' }
        };

        // Determine the ticks
        const maxTicks = 6;
        const tickInterval = Math.ceil(data.length / maxTicks);
        const tickvals = data.filter((_, i) => i % tickInterval === 0).map(d => d.date);
        const ticktext = tickvals.map(d => new Date(d).toISOString().slice(0, 7));

        const initialPlotData = [initialTracePositive, initialTraceNegative];

        const layout = {
            xaxis: {
                title: '<b>Date</b>',
                type: 'category',
                tickvals: tickvals,
                ticktext: ticktext,
                tickangle: -45
            },
            yaxis: {
                title: '<b>Sentiment Score %</b>',
                range: [-1, 1], // Start with a fixed range
                tickformat: '.1f'
            },
            barmode: 'relative',
            showlegend: true
        };

        // Initial plot with y-values set to 0
        Plotly.newPlot('chart-display', initialPlotData, layout, { displayModeBar: true });

        // Add click event listener to the chart
        document.getElementById('chart-display').on('plotly_click', (data) => {
            if (data.points.length > 0) {
                const point = data.points[0];
                const date = point.x;
                const sentimentDataForDate = sentimentData.filter(d => d.date === date);
                const articleHeadings = sentimentDataForDate.map(d => d.headline);
                const articleLinks = sentimentDataForDate.map(d => d.link);
                const positiveScores = sentimentDataForDate.map(d => d.positive_sentiment);
                const negativeScores = sentimentDataForDate.map(d => d.negative_sentiment);
                const uniqueIds = sentimentDataForDate.map(d => d.unique_id);

                const positiveLinks = [];
                const negativeLinks = [];
                const uniquePositiveIds = new Set(); // Set to track unique positive IDs
                const uniqueNegativeIds = new Set(); // Set to track unique negative IDs

                for (let i = 0; i < articleHeadings.length; i++) {
                    if (positiveScores[i] > negativeScores[i]) {
                        if (!uniquePositiveIds.has(uniqueIds[i])) {
                            uniquePositiveIds.add(uniqueIds[i]); // Add unique ID to the set
                            positiveLinks.push(`<li><a href="${articleLinks[i]}" target="_blank">${articleHeadings[i]}</a></li>`);
                        }
                    } else if (negativeScores[i] > positiveScores[i]) {
                        if (!uniqueNegativeIds.has(uniqueIds[i])) {
                            uniqueNegativeIds.add(uniqueIds[i]); // Add unique ID to the set
                            negativeLinks.push(`<li><a href="${articleLinks[i]}" target="_blank">${articleHeadings[i]}</a></li>`);
                        }
                    }
                }

                document.getElementById('positive_links').innerHTML = `
                    <h3>Positive Articles <span class="date-range">${date}</span></h3>
                    <ul>${positiveLinks.join('')}</ul>
                `;

                document.getElementById('negative_links').innerHTML = `
                    <h3>Negative Articles <span class="date-range">${date}</span></h3>
                    <ul>${negativeLinks.join('')}</ul>
                `;
            }
        });
          
        // Animate the bars to their actual values
        setTimeout(() => {
            Plotly.animate('chart-display', {
                data: [finalTracePositive, finalTraceNegative],
                traces: [0, 1],
                layout: layout
            }, {
                transition: {
                    duration: 1000,
                    easing: 'cubic-in-out'
                },
                frame: {
                    duration: 1000,
                    redraw: false
                }
            });

            // Smooth transition for autoscaling
            setTimeout(() => {
                const maxPositive = Math.max(...data.map(d => d.positive_sentiment));
                const maxNegative = Math.max(...data.map(d => d.negative_sentiment));
                const maxY = Math.max(maxPositive, maxNegative);

                Plotly.animate('chart-display', {
                    layout: {
                        yaxis: {
                            range: [-maxY - 0.1, maxY + 0.1]
                        }
                    }
                }, {
                    transition: {
                        duration: 500,
                        easing: 'cubic-in-out'
                    },
                    frame: {
                        duration: 500,
                        redraw: false
                    }
                });
            }, 600);
        }, 500);

        createSentimentGaugeChart("pie-chart", sentimentData)
    })
    .finally(() => {
        // Hide loading animation after chart is rendered
        clearLoader();
        document.getElementById('loading').style.display = 'none';
        document.getElementById('gauge-loading').style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
        
        // re-enable  
        analyzeButton.innerText = 'Analyse Sentiment';
        analyzeButton.classList.remove('analyzing');
        analyzeButton.disabled = false;

        document.getElementById('loading').style.display = 'none'; // Ensure to hide animation on error
        document.getElementById('gauge-loading').style.display = 'none';
        clearLoader();
    });
}

// Function to handle report generation
function generateReport(companyName, sentimentData) {
    
    // Generating animation
    const generateButton = document.querySelector('.generate-btn');
    generateButton.innerText = 'Generating...';
    generateButton.classList.add('generating'); // Add the generating class
    generateButton.disabled = true;

    fetch('/generate-report', {
        method: 'POST',
        body: JSON.stringify({ companyName, analysedData: sentimentData }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.blob())  // Expect the response as a blob (HTML file)
    .then(blob => {

        // Reset the button text and class
        generateButton.innerText = 'Generate Report';
        generateButton.classList.remove('generating'); // Remove the generating class
        generateButton.disabled = false;

        // Create a link to download the HTML report
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${companyName}_financial_report.html`;  // File name with company name
        link.click();
    })
    .catch(error => {
        console.error('Error generating the report:', error);
        // Reset the button text and class in case of error
        generateButton.innerText = 'Generate Report';
        generateButton.classList.remove('generating'); // Remove the generating class
        generateButton.disabled = false;
    });
}

function createSentimentGaugeChart(containerId, sentimentData) {
    // Calculate mean scores
    var totalPositive = 0, totalNegative = 0, totalNeutral = 0;
    var numEntries = sentimentData.length;

    sentimentData.forEach(entry => {
        totalPositive += entry.positive_sentiment;
        totalNegative += entry.negative_sentiment;
        totalNeutral += entry.neutral_sentiment;
    });

    var meanPositive = totalPositive / numEntries;
    var meanNegative = totalNegative / numEntries;
    var meanNeutral = totalNeutral / numEntries;

    var sentiments = {
        positive: meanPositive,
        negative: meanNegative,
        neutral: meanNeutral
    };

    var currentSentiment = 'positive'; // Default to positive

    function createGauge(sentimentType) {
        var colors = {
            positive: 'green',
            negative: 'red',
            neutral: 'gray'
        };
    
        var data = [
            {
                type: "indicator",
                mode: "gauge+number",
                value: 0, // Initially plot with a value of 0
                number: { 
                    valueformat: ".0f", // Format the value as a percentage
                    suffix: "%",
                    font: { size: 18, color: colors[sentimentType] } // Color the value
                },
                gauge: {
                    axis: { range: [0, 100], tickwidth: 1, tickcolor: "black" },
                    bar: { color: colors[sentimentType] },
                    bgcolor: "white",
                    borderwidth: 2,
                    bordercolor: "gray"
                }
            }
        ];
    
        var container = document.getElementById(containerId)
        var layout = {
            width: container.offsetWidth + 100,
            height: container.offsetHeight + 50,
            margin: { t: 25, r: 35, l: 25, b: 25 },
            paper_bgcolor: "white",
            font: { color: "black", family: "Arial" },
            annotations: [
                {
                    text: sentimentType.charAt(0).toUpperCase() + sentimentType.slice(1),
                    x: 0.5,
                    y: -0.1, 
                    showarrow: false,
                    font: { 
                        size: 20, 
                        color: colors[sentimentType], 
                        weight: "bold" // Added weight: "bold" to make the text bold
                    },
                    xref: 'paper',
                    yref: 'paper',
                    align: 'center'
                }
            ]
        };
    
        Plotly.newPlot(containerId, data, layout);
    
        // Animate the gauge to the actual value
        setTimeout(() => {
            var newData = [
                {
                    type: "indicator",
                    mode: "gauge+number",
                    value: sentiments[sentimentType],
                    number: {
                        valueformat: ".0f", // Format the value as a percentage
                        suffix: "%",
                        font: { size: 20, color: colors[sentimentType] } // Color the value
                    },
                    gauge: {
                        axis: { range: [0, 100], tickwidth: 1, tickcolor: "black" },
                        bar: { color: colors[sentimentType] },
                        bgcolor: "white",
                        borderwidth: 2,
                        bordercolor: "gray"
                    }
                }
            ];
    
            Plotly.animate(containerId, {
                data: newData,
                traces: [0],
                transition: {
                    duration: 1000,
                    easing: 'cubic-in-out'
                }
            });
        }, 1000);
    }

    function updateGauge() {
        switch (currentSentiment) {
            case 'positive':
                currentSentiment = 'negative';
                break;
            case 'negative':
                currentSentiment = 'neutral';
                break;
            case 'neutral':
                currentSentiment = 'positive';
                break;
        }
        
        var colors = {
            positive: 'green',
            negative: 'red',
            neutral: 'gray'
        };

        var newData = [
            {
                type: "indicator",
                mode: "gauge+number",
                value: sentiments[currentSentiment],
                number: {
                    valueformat: ".0f", // Format the value as a percentage
                    suffix: "%",
                    font: { size: 20, color: colors[currentSentiment] } // Color the value
                },
                gauge: {
                    axis: { range: [0, 100], tickwidth: 1, tickcolor: "black" },
                    bar: { color: colors[currentSentiment] },
                    bgcolor: "white",
                    borderwidth: 2,
                    bordercolor: "gray"
                }
            }
        ];

        Plotly.animate(containerId, {
            data: newData,
            traces: [0],
            layout: {
                annotations: [
                    {
                        text: currentSentiment.charAt(0).toUpperCase() + currentSentiment.slice(1),
                        x: 0.5,
                        y: -0.1, // Adjusted to be below the gauge
                        showarrow: false,
                        font: { size: 18, color: colors[currentSentiment], weight:"bold"},
                        xref: 'paper',
                        yref: 'paper',
                        align: 'center'
                    }
                ]
            },
            transition: {
                duration: 500,
                easing: 'cubic-in-out'
            }
        });
    }

    // Initial plot
    createGauge(currentSentiment);

    // Add click event to switch gauges
    document.getElementById(containerId).addEventListener('click', updateGauge);
}

function resetContent() {
    document.getElementById('positive_links').innerHTML = '<h3>Positive Articles</h3>';
    document.getElementById('negative_links').innerHTML = '<h3>Negative Articles</h3>';
    document.getElementById('Best_score').textContent = '--%';
    document.getElementById('Worst_score').textContent = '--%';
    document.getElementById('Best_score_date').textContent = 'YYYY-MM-DD';
    document.getElementById('Worst_score_date').textContent = 'YYYY-MM-DD';
}

// Advanced Loading animation
const processingStages = [
    { icon: '🔗', text: "Scraping Links", description: "Collecting web resources...", stageDuration: 0.1 },
    { icon: '🌐', text: "Resolving Links", description: "Validating and preparing links...", stageDuration: 0.1 },
    { icon: '📄', text: "Extracting Article Content", description: "Pulling text from web pages...", stageDuration: 0.1 },
    { icon: '🔍', text: "Analyzing Articles", description: "Processing textual insights...", stageDuration: 0.25 },
    { icon: '📊', text: "Plotting Sentiment Scores", description: "Generating sentiment visualization...", stageDuration: 0.25 },
    { icon: '✅', text: "Analysis Complete", description: "Finalizing results...", stageDuration: 0.2 }
];

const duration = 180000; // 3 minutes
const loaderIcon = document.getElementById('loaderIcon');
const stageText = document.getElementById('stageText');
const stageDescription = document.getElementById('stageDescription');
const overallProgressBar = document.getElementById('overallProgressBar');
const overallProgressText = document.getElementById('overallProgressText');
const stageProgressBar = document.getElementById('stageProgressBar');
const stageProgressText = document.getElementById('stageProgressText');

let progressInterval; // Declare a global variable to track the interval

function clearLoader() {
    // Reset progress bars and text to their initial state
    overallProgressBar.style.width = '0%';
    overallProgressText.textContent = '0%';
    stageProgressBar.style.width = '0%';
    stageProgressText.textContent = '0%';

    // Reset loader icon and text
    loaderIcon.textContent = '🔗';
    stageText.textContent = 'Scraping Links';
    stageDescription.textContent = 'Collecting web resources...';

    // Clear any existing interval
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null; // Ensure no residual references
    }
}

function updateLoader() {
    clearLoader(); // Ensure previous intervals are cleared before starting a new one

    const startTime = Date.now();

    progressInterval = setInterval(() => {
        const elapsedTime = Date.now() - startTime;
        const calculatedOverallProgress = Math.min((elapsedTime / duration) * 100, 100);

        const stageProgressPoints = processingStages.reduce((acc, stage, index) => {
            const prevProgress = index === 0 ? 0 : acc[index - 1];
            return [...acc, prevProgress + stage.stageDuration * 100];
        }, []);

        const currentStageIndex = stageProgressPoints.findIndex(
            (point) => calculatedOverallProgress < point
        );
        const activeStage = currentStageIndex !== -1 ? currentStageIndex : processingStages.length - 1;

        const currentStage = processingStages[activeStage];
        loaderIcon.textContent = currentStage.icon;
        stageText.textContent = currentStage.text;
        stageDescription.textContent = currentStage.description;

        const stageStartProgress = stageProgressPoints[activeStage - 1] || 0;
        const stageEndProgress = stageProgressPoints[activeStage];
        const currentStageTotalDuration = stageEndProgress - stageStartProgress;

        const relativeProgress = Math.max(
            0, 
            Math.min(
                100, 
                ((calculatedOverallProgress - stageStartProgress) / currentStageTotalDuration) * 100
            )
        );

        overallProgressBar.style.width = `${calculatedOverallProgress}%`;
        overallProgressText.textContent = `${Math.round(calculatedOverallProgress)}%`;

        stageProgressBar.style.width = `${relativeProgress}%`;
        stageProgressText.textContent = `${Math.round(relativeProgress)}%`;

        if (calculatedOverallProgress >= 100) {
            clearInterval(progressInterval);
            progressInterval = null; // Ensure no residual references
        }
    }, 100);
}
