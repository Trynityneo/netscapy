#!/usr/bin/env python3
"""
Network Mapping and Scanning Tool

A Python-based tool that performs network scanning and enumeration by wrapping
common security tools like Nmap, Nikto, and WhatWeb.
"""

import argparse
import json
import sys
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

# Import scanner modules
from tools.nmap_scanner import NmapScanner
from tools.nikto_scanner import NiktoScanner
from tools.whatweb_scanner import WhatWebScanner
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

# Tool registry
TOOL_REGISTRY = {
    'nmap': {
        'class': NmapScanner,
        'default_args': '-sV -sC -T4',
        'description': 'Port and service scanning with Nmap'
    },
    'nikto': {
        'class': NiktoScanner,
        'default_args': '-h',
        'description': 'Web server scanning with Nikto'
    },
    'whatweb': {
        'class': WhatWebScanner,
        'default_args': '--color=never --no-errors -a 3',
        'description': 'Web technology fingerprinting with WhatWeb'
    }
}

class NetworkScanner:
    def __init__(self, target: str, output_dir: str = "output/reports"):
        """
        Initialize the network scanner
        
        Args:
            target: Target IP or hostname to scan
            output_dir: Directory to store scan results
        """
        self.target = target
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Any] = {
            'target': target,
            'scans': {},
            'metadata': {
                'start_time': None,
                'end_time': None,
                'tools_used': []
            }
        }
    
    def run_scan(self, tool_name: str, tool_args: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a single scan with the specified tool
        
        Args:
            tool_name: Name of the tool to use (must be in TOOL_REGISTRY)
            tool_args: Optional arguments to pass to the tool
            
        Returns:
            Dict containing the scan results
        """
        if tool_name not in TOOL_REGISTRY:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_config = TOOL_REGISTRY[tool_name]
        tool_class = tool_config['class']
        
        # Use provided args or default args if none provided
        args = tool_args if tool_args is not None else tool_config.get('default_args', '')
        
        logger.info(f"Running {tool_name} scan on {self.target} with args: {args}")
        
        try:
            # Initialize and run the scanner
            scanner = tool_class(self.target, str(self.output_dir))
            result = scanner.run_scan(args)
            
            # Save results
            output_file = self.output_dir / f"{tool_name}_results_{self.target.replace('/', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"{tool_name} scan completed. Results saved to {output_file}")
            
            # Store results
            self.results['scans'][tool_name] = {
                'status': result.get('status', 'unknown'),
                'results_file': str(output_file),
                'error': result.get('error')
            }
            
            if tool_name not in self.results['metadata']['tools_used']:
                self.results['metadata']['tools_used'].append(tool_name)
            
            return result
            
        except Exception as e:
            error_msg = f"Error running {tool_name}: {str(e)}"
            logger.error(error_msg)
            
            self.results['scans'][tool_name] = {
                'status': 'failed',
                'error': error_msg
            }
            
            if tool_name not in self.results['metadata']['tools_used']:
                self.results['metadata']['tools_used'].append(tool_name)
            
            return {'error': error_msg}
    
    def run_scans(self, tools: List[str], tool_args: Optional[Dict[str, str]] = None, max_workers: int = 3) -> Dict[str, Any]:
        """
        Run multiple scans in parallel
        
        Args:
            tools: List of tool names to run
            tool_args: Optional dict mapping tool names to their arguments
            max_workers: Maximum number of concurrent scans
            
        Returns:
            Dict containing combined results from all scans
        """
        if tool_args is None:
            tool_args = {}
        
        # Filter out unknown tools
        valid_tools = [t for t in tools if t in TOOL_REGISTRY]
        unknown_tools = set(tools) - set(valid_tools)
        
        if unknown_tools:
            logger.warning(f"Unknown tools will be skipped: {', '.join(unknown_tools)}")
        
        if not valid_tools:
            raise ValueError("No valid tools specified")
        
        # Update metadata
        self.results['metadata']['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Run scans in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for tool in valid_tools:
                args = tool_args.get(tool, None)
                future = executor.submit(self.run_scan, tool, args)
                futures.append(future)
            
            # Wait for all scans to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Scan failed: {str(e)}")
        
        # Update metadata
        self.results['metadata']['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Save combined results
        combined_file = self.output_dir / f"combined_results_{self.target.replace('/', '_')}.json"
        with open(combined_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"All scans completed. Combined results saved to {combined_file}")
        
        return self.results

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Network Mapping and Scanning Tool',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'target',
        help='Target IP address or hostname to scan'
    )
    
    parser.add_argument(
        '--tools',
        nargs='+',
        choices=list(TOOL_REGISTRY.keys()),
        default=['nmap'],
        help='Tools to run (space-separated)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output/reports',
        help='Directory to save scan results'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=3,
        help='Maximum number of concurrent scans'
    )
    
    # Add tool-specific argument groups
    for tool, config in TOOL_REGISTRY.items():
        group = parser.add_argument_group(f"{tool} options")
        group.add_argument(
            f"--{tool}-args",
            default=config.get('default_args', ''),
            help=f"Arguments for {tool}: {config['description']}"
        )
    
    return parser.parse_args()

def main():
    """Main function"""
    try:
        args = parse_arguments()
        
        # Create scanner instance
        scanner = NetworkScanner(args.target, args.output_dir)
        
        # Prepare tool arguments
        tool_args = {}
        for tool in TOOL_REGISTRY.keys():
            arg_name = f"{tool}_args"
            if hasattr(args, arg_name):
                tool_args[tool] = getattr(args, arg_name)
        
        # Run scans
        scanner.run_scans(args.tools, tool_args, args.max_workers)
        
        print(f"\nScan completed! Results saved to: {args.output_dir}")
        
    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
