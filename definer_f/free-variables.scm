(define-module (well-posed free-variables))

(use-modules (language tree-il)
	     (ice-9 optargs))

(define (flatten x)
    (cond ((null? x) '())
          ((not (pair? x)) (list x))
          (else (append (flatten (car x))
                        (flatten (cdr x))))))
 
;;;
;;; A stack of "environments" is just a list of lists
;;; Each inner list contains defined symbols in a scope,
;;; one scope per list
(define %in-any-env-stack
  (lambda (x env-stack)
    (if (null? env-stack)
	#f
	(if (member x (car env-stack))
	    #t
	    (%in-any-env-stack x (cdr env-stack))))))

;;;
;;; returns a list of free variables given a core expanded expression.
;;; This means that the expression consists of only scheme core
;;; syntax and is devoid of macros :)
(define %compute-free-variables-on-core-expression
  (lambda (expr env-stack)
    (if (null? expr)
	'()
	(if (not (pair? expr))
	    (if (or (not (symbol? expr))
		    (%in-any-env-stack expr env-stack))
		'()
		(if (defined? expr)
		    '()
		    (list expr)))
	    (cond
	     ((equal? (car expr) 'lambda)
	      (%compute-free-variables-on-core-expression
	       (cdr (cdr expr))
	       (cons
		(cadr expr)
		env-stack)))
	     ((member (car expr)
		      '(let let* letrec parameterize fluid-let ))
	      (%compute-free-variables-on-core-expression
	       (cdr (cdr expr))
	       (cons (map (lambda (x)
			    (if (pair? x)
				(car x)
				x))
			  (car (cdr expr)))
		     env-stack)))
	     ((equal? (car expr) 'define)
	      (if (pair? (car (cdr expr)))
		  (%compute-free-variables-on-core-expression
		   (cdr (cdr expr))
		   (cons (car (cdr expr))
			 env-stack))
		  (%compute-free-variables-on-core-expression
		   (cdr (cdr expr))
		   (cons (list (car (cdr expr)))
			 env-stack))))
	     ((equal? (car expr) 'set!)
	      (%compute-free-variables-on-core-expression
	       (cdr (cdr expr))
	       (cons (list (car (cdr expr)))
		     env-stack)))
	     ((member (car expr) '(quote quasiquote))
	      '())
	     (else
	      (flatten
	       (map (lambda (x)
		      (%compute-free-variables-on-core-expression
		       x
		       env-stack))
		    expr))))))))




;;;
;;; Returns a lsit of free variables (as symbols)
;;; within the given scheme code (unevaluated)
(define compute-free-variables
  (lambda* (expr #:optional (expand-mode 'e) (expand-expander-when '(eval)))
    (let ((core-expr (tree-il->scheme
		      (macroexpand expr expand-mode expand-expander-when))))
      (%compute-free-variables-on-core-expression
       core-expr
       '()))))
(export compute-free-variables)
		 



	       
