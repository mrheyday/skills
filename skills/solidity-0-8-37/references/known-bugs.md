# List of Known Bugs (3.25)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

- 3.25 List of Known Bugs

---

# 3.25 List of Known Bugs

Below, you can find a JSON-formatted list of some of the known security-relevant bugs in the Solidity compiler. The file itself is hosted in the GitHub repository. The list stretches back as far as version 0.3.0, bugs known to be present only in versions preceding that are not listed. (https://github.com/argotorg/solidity/blob/develop/docs/bugs.json)

There is another file called bugs_by_version.json, which can be used to check which bugs affect a specific version of (https://github.com/argotorg/solidity/blob/develop/docs/bugs_by_version.json)

the compiler.

Contract source verification tools and also other tools interacting with contracts should consult this list according to the following criteria:

- It is mildly suspicious if a contract was compiled with a nightly compiler version instead of a released version. This list does not keep track of unreleased or nightly versions.

- It is also mildly suspicious if a contract was compiled with a version that was not the most recent at the time the contract was created. For contracts created from other contracts, you have to follow the creation chain back to a transaction and use the date of that transaction as creation date.

- It is highly suspicious if a contract was compiled with a compiler that contains a known bug and the contract was created at a time where a newer compiler version containing a fix was already released.

The JSON file of known bugs below is an array of objects, one for each bug, with the following keys:

Unique identifier given to the bug in the form of SOL-<year>-<number>. It is possible that multiple entries exists with the same uid. This means multiple version ranges are affected by the same bug.

Unique name given to the bug

Short description of the bug

Detailed description of the bug

URL of a website with more detailed information, optional

The first published compiler version that contained the bug, optional

### uid

### name

### summary

### description

### link

### introduced

### fixed

The first published compiler version that did not contain the bug anymore

### publish

The date at which the bug became known publicly, optional

Severity of the bug: very low, low, medium, high. Takes into account discoverability in contract tests, likelihood of occurrence and potential damage by exploits.

Conditions that have to be met to trigger the bug. The following keys can be used: optimizer, Boolean value which means that the optimizer has to be switched on to enable the bug. evmVersion, a string that indicates whichEVMversion compiler settings trigger the bug. The string can contain comparison operators. For example, ">=constantinople" means that the bug is present when the EVM version is set to constantinople or later. If no conditions are given, assume that the bug is present.

This field contains different checks that report whether the smart contract contains the bug or not. The first type of check are JavaScript regular expressions that are to be matched against the source code (“source-regex”) if the bug is present. If there is no match, then the bug is very likely not present. If there is a match, the bug might be present. For improved accuracy, the checks should be applied to the source code after stripping comments. The second type of check are patterns to be checked on the compact AST of the Solidity program (“ast-compact-json-path”). The specified search query is a JsonPath expression. If at least one path of the Solidity AST matches the query, the bug is likely present. (https://github.com/json-path/JsonPath)

### severity

### conditions

### check

```
[
{
"uid": "SOL-2026-6",
"name": "MisorderedNamedParametersInRequireWithCustomErrors",
"summary": "Custom error arguments passed to ``require`` using named-parametersyntax are ABI-encoded in call-site order instead of declaration order when compilingvia IR.",
"description": "When a custom error is passed as the second argument of``require`` and instantiated using named-parameter syntax (e.g., ``require(cond,MyError({b: 1, a: 2}))``), the IR-based code generator encoded the arguments in theorder they appeared at the call site rather than reordering them to match theparameter order declared in the error definition. The arguments are still type-checkedagainst their named slots, but the type system does not require the call-site order tomatch the declaration, so the bug could be triggered even when the supplied valueswould type-check in either order. When all arguments occupied the same number of stackslots (e.g., all single-slot value types), the resulting payload could contain thevalues in the wrong positions for the error's signature. When the call-site argumenttypes differed in stack-slot width (for example a ``calldata`` reference next to avalue type), the misordering also misaligned the helper's parameters slot-by-slot,producing a payload of an entirely different shape than the error's ABI signature —values landed in unrelated positions, dynamic-type lengths were read from arbitrarystack values, and string/bytes data could be copied from arbitrary calldata offsets.In the best case this triggered an EVM-level error during encoding; in the worst casea structurally valid payload containing wrong data was encoded successfully. The bugwas specific to custom errors passed as the second argument of ``require``. Standalone``revert ErrorName({...})`` statements, event emissions, function calls, structconstructor invocations and other constructs supporting named parameters were not affected. The evmasm pipeline was also unaffected.",
"link": "https://blog.soliditylang.org/2026/09/10/misordered-named-parameters-in-
```

``` require-with-custom-errors-bug/",
"introduced": "0.8.26",
"fixed": "0.8.37",
"severity": "very low",
"conditions": {
"viaIR": true
}
},
{
"uid": "SOL-2026-5",
"name": "MemoryByteArrayElementDeleteClearsWholeWord",
"summary": "Applying ``delete`` to a single element of a ``bytes`` array inmemory clears not only that element but the whole 32-byte word starting at the element 's location, zeroing up to 31 bytes beyond the element.",
"description": "Elements of ``bytes`` arrays in memory are packed, eachoccupying a single byte. When a value is assigned to such an element, the evmasm codegenerator correctly stores it with a single-byte ``MSTORE8`` instruction. The codepath in the evmasm pipeline implementing ``delete`` on such an element, however, wrotethe zero value with a full-word ``MSTORE``, clearing the 32 bytes starting at theelement's location. The bytes following the element within the array were silentlyzeroed. If the element was within the last 31 bytes of the array's allocation, thewrite also extended past it into the area where the allocator places the next memoryobject, clearing the most significant bytes of that object's first word. How manyelements are in reach depends on the size of the allocation: arrays created with ``newbytes(n)`` or from literals occupy their length rounded up to a multiple of 32 bytes,so only elements falling within the last 31 bytes of that rounded-up area, if any,could be affected. The results of ``bytes.concat``, ``string.concat``, and the ``abi.encode*`` functions, on the other hand, are placed by the evmasm pipeline in anallocation of exactly the size of their data, so the next object starts immediatelyafter their last element and each of their last 31 elements is in reach. Assigningzero to an element (``b[i] = 0``) was not affected, only the ``delete`` operator, andneither were byte arrays in transient storage, storage, or calldata. The bug existsonly in the evmasm pipeline. Code compiled via IR is unaffected. Optimizer settingshave no influence. The defective code predates the first released version of the compiler.",
"link": "https://blog.soliditylang.org/2026/09/10/memory-byte-array-element- delete-clears-whole-word-bug/",
"fixed": "0.8.37",
"severity": "low/medium",
"conditions": {
"viaIR": false
}
},
{
"uid": "SOL-2026-4",
"name": "SpillSlotCollisionAcrossMutualRecursion",
"summary": "Local variables of two simultaneously active functions moved tofixed memory offsets by the stack limit evader may be assigned the same offset if thecall graph contains mutual recursion, so that one variable is silently overwritten bythe other.",
"description": "To work around the 16-slot stack access limit of the EVM, the IR- based code generator can, under some preconditions, move local variables to fixed
memory offsets. Variables that can never be active at the same time may safely sharean offset, so the reserved memory area is sized by a depth-first walk of the callgraph that computes for every node the number of slots it and its callees need. Tokeep this walk from descending infinitely into recursive call chains, the slot countwas initialized with zero upon entering it. This provisional zero was observable: afunction reached again through a call graph cycle reported an empty footprint to itscaller, the caller's count was finalized and cached on that basis, and the undercountpropagated to every later caller, including functions outside the cycle. As a result,a function called by such a cycle and a function calling into it could be assigned thesame memory slot even though both can be active at the same time. A relocated variablestill needed after the call into the cycle returned had then been silently overwrittenby the called function, producing wrong results. Triggering the bug requires the IRpipeline and a call graph in which a cycle of at least two mutually recursivefunctions both reaches a function needing relocation of variables to memory and isentered from a separate call chain whose own relocated variable is read again afterthe call towards the cycle returns. From 0.8.21 onward, it is independent of whether the optimizer is enabled.",
"link": "https://blog.soliditylang.org/2026/09/10/spill-slot-collision-across- mutual-recursion-bug/",
"introduced": "0.7.2",
"fixed": "0.8.37",
"severity": "low/medium",
"conditions": {
"viaIR": true
}
},
{
"uid": "SOL-2026-3",
"name": "InheritanceOrderReversalOnStorageEndWarning",
"summary": "Emitting a warning about storage base location being too close tothe storage end unintentionally reversed the ``linearizedBaseContracts`` annotation,possibly leading to miscompilation due to reversing the order in which inheritance isresolved.",
"description": "When the compiler detects that a custom layout specifier putscontract's static storage area too close to the end of the address space, it emits awarning. To make the warning more useful, the compiler tries to point at the laststorage variable in that area. For this reason it walks the linearized inheritancehierarchy in reverse (from the least to the most derived). The list is calculated onceand stored in an AST annotation called ``linearizedBaseContracts``. The direct causeof the bug was the fact that the code that reverses the list was doing it in placerather than on a copy, modifying the annotation. This effectively reversed the orderof base contracts seen by any component that runs after layout checks: later phases ofanalysis, AST export, code generator, SMTChecker, etc. The observable effect was areversed order of state variable initialization, constructor invocation, virtualfunction/modifier resolution, leading either to miscompilations or internal compilererrors, depending on the specific usage. Since the source of the bug was in theanalysis stage, it was independent of the codegen pipeline or optimizer settings. Themain condition necessary to trigger the bug was the presence of the warning in theoutput. The other is presence of language constructs whose evaluation depends on theinheritance order. While potential effects are very serious, this requirement excludesthe vast majority of contracts as intentionally placing the storage variables in the last 2**64 slots is highly discouraged, which was actually the main reason for adding
```

``` this warning.",
"link": "https://blog.soliditylang.org/2026/07/09/inheritance-order-reversal-on- storage-end-warning-bug/",
"introduced": "0.8.29",
"fixed": "0.8.36",
"severity": "medium"
},
{
"uid": "SOL-2026-2",
"name": "UnsoundSpillInMutualRecursion",
"summary": "Local variables of a function involved in mutual recursion may spuriously be moved to fixed memory offsets and overwritten across recursive calls.",
"description": "To work around the 16-slot stack access limit of the EVM, the IR-based code generator can move local variables of stack-too-deep functions to fixedmemory offsets. This relocation is unsound for recursive functions: a fixed offsetwould be shared by all activations of the function, so a recursive call wouldoverwrite the caller's value. The stack limit evader therefore must not relocatevariables of functions that are part of a recursive call chain. To this end, the callgraph was searched for cycles using a path-based depth-first search that, once afunction had been fully explored and popped from the search path, short-circuited onit on any later visit. As a result, a function shared between several intersectingcycles could be reached first through a path that did not yet close a cycle through it, get marked as finished, and then be skipped when a later path would have revealedthat it does lie on a cycle. Such a function was misclassified as non-recursive. Whena misclassified function was complex enough for the stack limit evader to relocatesome of its variables, those variables were moved to fixed memory offsets and silentlycorrupted on recursion, producing wrong results rather than a compile-time error.Triggering the bug requires the IR pipeline, a set of mutually recursive functionswhose call graph contains intersecting cycles, at least one of the functions in anundetected part of a cycle being complex enough to require relocation to memory, andan unfortunate processing order of the functions (which depends on the hashes of their Yul names). It is independent of whether the optimizer is enabled.",
"link": "https://blog.soliditylang.org/2026/07/09/unsound-spill-in-mutual- recursion-bug/",
"introduced": "0.7.2",
"fixed": "0.8.36",
"severity": "medium",
"conditions": {
"viaIR": true
}
},
{
"uid": "SOL-2026-1",
"name": "TransientStorageClearingHelperCollision",
"summary": "Clearing both storage and transient storage variables in the same contract may result in only one of these locations being cleared.",
"description": "The IR-based code generator provides a set of Yul helperfunctions for basic operations, such as clearing, copying, encoding or typeconversions. Not all functions are used by every contract. The codegen appends them tothe generated sources individually, only when an operation that would invoke one ofthem is encountered. Utility functions are often specialized for different types and locations. Since Yul does not support generic functions, specialization is done by
generating multiple versions of the same function, with the information distinguishingthe variants embedded in their names. However, if not all the necessary bits ofdistinguishing information are properly accounted for, two helpers may end up with thesame name, causing a collision. In this situation the codegen includes only one ofthem, with calls to both variants invoking it. This happened with the ``set_to_zero``helper used when an area of transient or persistent storage needs to be cleared. Thehelper name was missing the location information, which resulted in a collisionbetween the persistent and transient storage variants for the same type. This meantthat contracts clearing both locations would actually clear only one, leaving theother untouched. Which location ended up being cleared depended on the order in whichthe code generator processed the input. The necessary condition to trigger the bug wasthe use of ``delete`` operator on a transient storage variable. This was due to valuetypes being the only types supported in transient storage and ``delete`` being theonly operation invoking the helper allowed on such types. The other necessarycondition was clearing of persistent storage and in this case the range of affectedoperations was wider: operator ``delete``, array ``pop()`` or assignment that resultedin a longer array being overwritten with a shorter one. The cleared variable itselfalso did not necessarily have to be of the same type. It was enough that a matchingvalue type was nested in it. It also did not always have to be the exact same valuetype - clearing operations on reference types are usually performed at slotgranularity, treating every slot as ``uint256`` rather than clearing every valuepacked into it individually. To trigger the bug both operations had to be presentwithin the same piece of bytecode. Independent contracts, not related throughinheritance, would not affect each other this way. The presence of one operation onlyin creation code and the other only in deployed code would not trigger the bug either.",
"link": "https://blog.soliditylang.org/2026/02/18/transient-storage-clearing- helper-collision-bug/",
"introduced": "0.8.28",
"fixed": "0.8.34",
"severity": "high",
"conditions": {
"viaIR": true,
"evmVersion": ">=cancun"
}
},
{
"uid": "SOL-2025-1",
"name": "LostStorageArrayWriteOnSlotOverflow",
"summary": "Operations that involve clearing or copying from arrays that straddle the end of storage could result in silent data retention.",
"description": "Solidity makes it possible to define variables that extend pastthe last (2**256-th) slot of storage, which results in wrap-around back to slot zero.Since EVM uses 256-bit integer arithmetic, most operations on such variables just work. The only situation which requires special attention is iteration against absoluteslot addresses: the invariant that the last slot belonging to a variable has thehighest address does not hold. When implemented incorrectly, a loop over an array willimmediately terminate if the container spans the end of storage - due to the initialposition already being greater than the end position. This affected storage arrayclearing loops generated by both evmasm and IR pipelines. Additionally, (only in theevmasm pipeline) copying operations whose source was an array straddling the end of storage were also affected. At the language level, the buggy code would be generated
for array assignment, array initialization, delete operator, <array>.pop() and <array>.push(). Note that a clearing loop is inserted by the compiler not only for invocationsof the delete operator, but also to zero storage when overwriting a longer array witha shorter one, popping an element or even pushing an empty element to a dynamic array.Since clearing is a separate loop, it is possible for the bug to only affect it andnot the copy operation it follows (which is always the case in the IR pipeline). Thebug is extremely unlikely to be triggered accidentally due to the probabilisticimpossibility of a short dynamic array being allocated right at the storage boundary.On the other hand, scenarios in which a user may place a static array thereintentionally do not seem realistic and are limited to unusual layouts, in which acontract does not place any storage variables at slot zero (otherwise they would overlap the array).",
"link": "https://blog.soliditylang.org/2025/12/18/lost-storage-array-write-on- slot-overflow-bug/",
"introduced": "0.1.0",
"fixed": "0.8.32",
"severity": "low"
},
{
"uid": "SOL-2023-3",
"name": "VerbatimInvalidDeduplication",
"summary": "All ``verbatim`` blocks are considered identical by deduplicator and can incorrectly be unified when surrounded by identical opcodes.",
"description": "The block deduplicator is a step of the opcode-based optimizerwhich identifies equivalent assembly blocks and merges them into a single one. However, when blocks contained ``verbatim``, their comparison was performed incorrectly,leading to the collapse of assembly blocks which are identical except for the contentsof the ``verbatim`` items. Since ``verbatim`` is only available in Yul, compilation of Solidity sources is not affected.",
"link": "https://blog.soliditylang.org/2023/11/08/verbatim-invalid-deduplication-bug/",
"introduced": "0.8.5",
"fixed": "0.8.23",
"severity": "low"
},
{
"uid": "SOL-2023-2",
"name": "FullInlinerNonExpressionSplitArgumentEvaluationOrder",
"summary": "Optimizer sequences containing FullInliner do not preserve theevaluation order of arguments of inlined function calls in code that is not in expression-split form.",
"description": "Function call arguments in Yul are evaluated right to left. Thisorder matters when the argument expressions have side-effects, and changing it maychange contract behavior. FullInliner is an optimizer step that can replace a functioncall with the body of that function. The transformation involves assigning argumentexpressions to temporary variables, which imposes an explicit evaluation order.FullInliner was written with the assumption that this order does not necessarily haveto match usual argument evaluation order because the argument expressions have no side-effects. In most circumstances this assumption is true because the defaultoptimization step sequence contains the ExpressionSplitter step. ExpressionSplitterensures that the code is in *expression-split form*, which means that function calls cannot appear nested inside expressions, and all function call arguments have to be
variables. The assumption is, however, not guaranteed to be true in general. Version 0.6.7 introduced a setting allowing users to specify an arbitrary optimization stepsequence, making it possible for the FullInliner to actually encounter argumentexpressions with side-effects, which can result in behavior differences betweenoptimized and unoptimized bytecode. Contracts compiled without optimization or withthe default optimization sequence are not affected. To trigger the bug the user has toexplicitly choose compiler settings that contain a sequence with FullInliner step not preceded by ExpressionSplitter.",
"link": "https://blog.soliditylang.org/2023/07/19/full-inliner-non-expression- split-argument-evaluation-order-bug/",
"introduced": "0.6.7",
"fixed": "0.8.21",
"severity": "low",
"conditions": {
"yulOptimizer": true
}
},
{
"uid": "SOL-2023-1",
"name": "MissingSideEffectsOnSelectorAccess",
"summary": "Accessing the ``.selector`` member on complex expressions leaves the expression unevaluated in the legacy code generation.",
"description": "When accessing the ``.selector`` member on an expression withside-effects, like an assignment, a function call or a conditional, the expressionwould not be evaluated in the legacy code generation. This would happen in expressionswhere the functions used in the expression were all known at compilation time,regardless of whether the whole expression could be evaluated at compilation time ornot. Note that the code generated by the IR pipeline was unaffected and would behave as expected.",
"link": "https://blog.soliditylang.org/2023/07/19/missing-side-effects-on- selector-access-bug/",
"introduced": "0.6.2",
"fixed": "0.8.21",
"severity": "low",
"conditions": {
"viaIR": false
}
},
{
"uid": "SOL-2022-7",
"name": "StorageWriteRemovalBeforeConditionalTermination",
"summary": "Calling functions that conditionally terminate the external EVM callusing the assembly statements ``return(...)`` or ``stop()`` may result in incorrect removals of prior storage writes.",
"description": "A call to a Yul function that conditionally terminates theexternal EVM call could result in prior storage writes being incorrectly removed bythe Yul optimizer. This used to happen in cases in which it would have been valid toremove the store, if the Yul function in question never actually terminated theexternal call, and the control flow always returned back to the caller instead.Conditional termination within the same Yul block instead of within a called functionwas not affected. In Solidity with optimized via-IR code generation, any storage write before a function conditionally calling ``return(...)`` or ``stop()`` in inline
assembly, may have been incorrectly removed, whenever it would have been valid toremove the write without the ``return(...)`` or ``stop()``. In optimized legacy codegeneration, only inline assembly that did not refer to any Solidity variables and that involved conditionally-terminating user-defined assembly functions could be affected.",
"link": "https://blog.soliditylang.org/2022/09/08/storage-write-removal-before- conditional-termination/",
"introduced": "0.8.13",
"fixed": "0.8.17",
"severity": "medium/high",
"conditions": {
"yulOptimizer": true
}
},
{
"uid": "SOL-2022-6",
"name": "AbiReencodingHeadOverflowWithStaticArrayCleanup",
"summary": "ABI-encoding a tuple with a statically-sized calldata array in thelast component would corrupt 32 leading bytes of its first dynamically encodedcomponent.",
"description": "When ABI-encoding a statically-sized calldata array, thecompiler always pads the data area to a multiple of 32-bytes and ensures that thepadding bytes are zeroed. In some cases, this cleanup used to be performed by alwayswriting exactly 32 bytes, regardless of how many needed to be zeroed. This was donewith the assumption that the data that would eventually occupy the area past the endof the array had not yet been written, because the encoder processes tuple componentsin the order they were given. While this assumption is mostly true, there is animportant corner case: dynamically encoded tuple components are stored separately fromthe statically-sized ones in an area called the *tail* of the encoding and the tailimmediately follows the *head*, which is where the statically-sized components areplaced. The aforementioned cleanup, if performed for the last component of the headwould cross into the tail and overwrite up to 32 bytes of the first component storedthere with zeros. The only array type for which the cleanup could actually result inan overwrite were arrays with ``uint256`` or ``bytes32`` as the base element type andin this case the size of the corrupted area was always exactly 32 bytes. The problemaffected tuples at any nesting level. This included also structs, which are encoded astuples in the ABI. Note also that lists of parameters and return values of functions, events and errors are encoded as tuples.",
"link": "https://blog.soliditylang.org/2022/08/08/calldata-tuple-reencoding-head- overflow-bug/",
"introduced": "0.5.8",
"fixed": "0.8.16",
"severity": "medium",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2022-5",
"name": "DirtyBytesArrayToStorage",
"summary": "Copying ``bytes`` arrays from memory or calldata to storage may result in dirty storage values.",
"description": "Copying ``bytes`` arrays from memory or calldata to storage is
done in chunks of 32 bytes even if the length is not a multiple of 32. Thereby, extrabytes past the end of the array may be copied from calldata or memory to storage.These dirty bytes may then become observable after a ``.push()`` without arguments tothe bytes array in storage, i.e. such a push will not result in a zero value at theend of the array as expected. This bug only affects the legacy code generation pipeline, the new code generation pipeline via IR is not affected.",
"link": "https://blog.soliditylang.org/2022/06/15/dirty-bytes-array-to-storage-bug/",
"introduced": "0.0.1",
"fixed": "0.8.15",
"severity": "low"
},
{
"uid": "SOL-2022-4",
"name": "InlineAssemblyMemorySideEffects",
"summary": "The Yul optimizer may incorrectly remove memory writes from inline assembly blocks, that do not access solidity variables.",
"description": "The Yul optimizer considers all memory writes in the outermostYul block that are never read from as unused and removes them. This is valid when thatYul block is the entire Yul program, which is always the case for the Yul codegenerated by the new via-IR pipeline. Inline assembly blocks are never optimized inisolation when using that pipeline. Instead they are optimized as a part of the wholeYul input. However, the legacy code generation pipeline (which is still the default)runs the Yul optimizer individually on an inline assembly block if the block does notrefer to any local variables defined in the surrounding Solidity code. Consequently,memory writes in such inline assembly blocks are removed as well, if the writtenmemory is never read from in the same assembly block, even if the written memory is accessed later, for example by a subsequent inline assembly block.",
"link": "https://blog.soliditylang.org/2022/06/15/inline-assembly-memory-side-effects-bug/",
"introduced": "0.8.13",
"fixed": "0.8.15",
"severity": "medium",
"conditions": {
"yulOptimizer": true
}
},
{
"uid": "SOL-2022-3",
"name": "DataLocationChangeInInternalOverride",
"summary": "It was possible to change the data location of the parameters orreturn variables from ``calldata`` to ``memory`` and vice-versa while overridinginternal and public functions. This caused invalid code to be generated when calling such a function internally through virtual function calls.",
"description": "When calling external functions, it is irrelevant if the datalocation of the parameters is ``calldata`` or ``memory``, the encoding of the datadoes not change. Because of that, changing the data location when overriding externalfunctions is allowed. The compiler incorrectly also allowed a change in the datalocation for overriding public and internal functions. Since public functions can becalled internally as well as externally, this causes invalid code to be generated whensuch an incorrectly overridden function is called internally through the base contract. The caller provides a memory pointer, but the called function interprets it as a
```

``` calldata pointer or vice-versa.",
"link": "https://blog.soliditylang.org/2022/05/17/data-location-inheritance-bug/",
"introduced": "0.6.9",
"fixed": "0.8.14",
"severity": "very low"
},
{
"uid": "SOL-2022-2",
"name": "NestedCalldataArrayAbiReencodingSizeValidation",
"summary": "ABI-reencoding of nested dynamic calldata arrays did not alwaysperform proper size checks against the size of calldata and could read beyond ``calldatasize()``.",
"description": "Calldata validation for nested dynamic types is deferred untilthe first access to the nested values. Such an access may for example be a copy tomemory or an index or member access to the outer type. While in most such accessescalldata validation correctly checks that the data area of the nested array iscompletely contained in the passed calldata (i.e. in the range [0, calldatasize()]),this check may not be performed, when ABI encoding such nested types again directlyfrom calldata. For instance, this can happen, if a value in calldata with a nesteddynamic array is passed to an external call, used in ``abi.encode`` or emitted asevent. In such cases, if the data area of the nested array extends beyond``calldatasize()``, ABI encoding it did not revert, but continued reading values from beyond ``calldatasize()`` (i.e. zero values).",
"link": "https://blog.soliditylang.org/2022/05/17/calldata-reencode-size-check-bug/",
"introduced": "0.5.8",
"fixed": "0.8.14",
"severity": "very low"
},
{
"uid": "SOL-2022-1",
"name": "AbiEncodeCallLiteralAsFixedBytesBug",
"summary": "Literals used for a fixed length bytes parameter in ``abi. encodeCall`` were encoded incorrectly.",
"description": "For the encoding, the compiler only considered the types of theexpressions in the second argument of ``abi.encodeCall`` itself, but not the parametertypes of the function given as first argument. In almost all cases the abi encoding ofthe type of the expression matches the abi encoding of the parameter type of the givenfunction. This is because the type checker ensures the expression is implicitlyconvertible to the respective parameter type. However this is not true for numberliterals used for fixed bytes types shorter than 32 bytes, nor for string literalsused for any fixed bytes type. Number literals were encoded as numbers instead ofbeing shifted to become left-aligned. String literals were encoded as dynamically sized memory strings instead of being converted to a left-aligned bytes value.",
"link": "https://blog.soliditylang.org/2022/03/16/encodecall-bug/",
"introduced": "0.8.11",
"fixed": "0.8.13",
"severity": "very low"
},
{
"uid": "SOL-2021-4",
"name": "UserDefinedValueTypesBug",
"summary": "User defined value types with underlying type shorter than 32 bytes used incorrect storage layout and wasted storage",
"description": "The compiler did not correctly compute the storage layout ofuser defined value types based on types that are shorter than 32 bytes. It wouldalways use a full storage slot for these types, even if the underlying type was shorter. This was wasteful and might have problems with tooling or contract upgrades.",
"link": "https://blog.soliditylang.org/2021/09/29/user-defined-value-types-bug/",
"introduced": "0.8.8",
"fixed": "0.8.9",
"severity": "very low"
},
{
"uid": "SOL-2021-3",
"name": "SignedImmutables",
"summary": "Immutable variables of signed integer type shorter than 256 bits can lead to values with invalid higher order bits if inline assembly is used.",
"description": "When immutable variables of signed integer type shorter than 256bits are read, their higher order bits were unconditionally set to zero. The correctoperation would be to sign-extend the value, i.e. set the higher order bits to one ifthe sign bit is one. This sign-extension is performed by Solidity just prior to whenit matters, i.e. when a value is stored in memory, when it is compared or when adivision is performed. Because of that, to our knowledge, the only way to access the value in its unclean state is by reading it through inline assembly.",
"link": "https://blog.soliditylang.org/2021/09/29/signed-immutables-bug/",
"introduced": "0.6.5",
"fixed": "0.8.9",
"severity": "very low"
},
{
"uid": "SOL-2021-2",
"name": "ABIDecodeTwoDimensionalArrayMemory",
"summary": "If used on memory byte arrays, result of the function ``abi.decode``can depend on the contents of memory outside of the actual byte array that is decoded.",
"description": "The ABI specification uses pointers to data areas for everythingthat is dynamically-sized. When decoding data from memory (instead of calldata), theABI decoder did not properly validate some of these pointers. More specifically, itwas possible to use large values for the pointers inside arrays such that computingthe offset resulted in an undetected overflow. This could lead to these pointerstargeting areas in memory outside of the actual area to be decoded. This way, it waspossible for ``abi.decode`` to return different values for the same encoded byte array.",
"link": "https://blog.soliditylang.org/2021/04/21/decoding-from-memory-bug/",
"introduced": "0.4.16",
"fixed": "0.8.4",
"conditions": {
"ABIEncoderV2": true
},
"severity": "very low"
},
{
"uid": "SOL-2021-1",
"name": "KeccakCaching",
"summary": "The bytecode optimizer incorrectly reused previously evaluatedKeccak-256 hashes. You are unlikely to be affected if you do not compute Keccak-256 hashes in inline assembly.",
"description": "Solidity's bytecode optimizer has a step that can compute Keccak-256 hashes, if the contents of the memory are known during compilation time. This stepalso has a mechanism to determine that two Keccak-256 hashes are equal even if thevalues in memory are not known during compile time. This mechanism had a bug whereKeccak-256 of the same memory content, but different sizes were considered equal. Morespecifically, ``keccak256(mpos1, length1)`` and ``keccak256(mpos2, length2)`` in somecases were considered equal if ``length1`` and ``length2``, when rounded up to nearestmultiple of 32 were the same, and when the memory contents at ``mpos1`` and ``mpos2``can be deduced to be equal. You maybe affected if you compute multiple Keccak-256hashes of the same content, but with different lengths inside inline assembly. You areunaffected if your code uses ``keccak256`` with a length that is not a compile-time constant or if it is always a multiple of 32.",
"link": "https://blog.soliditylang.org/2021/03/23/keccak-optimizer-bug/",
"fixed": "0.8.3",
"conditions": {
"optimizer": true
},
"severity": "medium"
},
{
"uid": "SOL-2020-11",
"name": "EmptyByteArrayCopy",
"summary": "Copying an empty byte array (or string) from memory or calldata tostorage can result in data corruption if the target array's length is increased subsequently without storing new data.",
"description": "The routine that copies byte arrays from memory or calldata tostorage stores unrelated data from after the source array in the storage slot if thesource array is empty. If the storage array's length is subsequently increased eitherby using ``.push()`` or by assigning to its ``.length`` attribute (only before 0.6.0),the newly created byte array elements will not be zero-initialized, but contain theunrelated data. You are not affected if you do not assign to ``.length`` and do notuse ``.push()`` on byte arrays, or only use ``.push(<arg>)`` or manually initialize the new elements.",
"link": "https://blog.soliditylang.org/2020/10/19/empty-byte-array-copy-bug/",
"fixed": "0.7.4",
"severity": "medium"
},
{
"uid": "SOL-2020-10",
"name": "DynamicArrayCleanup",
"summary": "When assigning a dynamically-sized array with types of size at most16 bytes in storage causing the assigned array to shrink, some parts of deleted slots were not zeroed out.",
"description": "Consider a dynamically-sized array in storage whose base-type issmall enough such that multiple values can be packed into a single slot, such as `uint128[]`. Let us define its length to be `l`. When this array gets assigned from
another array with a smaller length, say `m`, the slots between elements `m` and `l`have to be cleaned by zeroing them out. However, this cleaning was not performedproperly. Specifically, after the slot corresponding to `m`, only the first packedvalue was cleaned up. If this array gets resized to a length larger than `m`, theindices corresponding to the unclean parts of the slot contained the original value,instead of 0. The resizing here is performed by assigning to the array `length`, by a`push()` or via inline assembly. You are not affected if you are only using `.push(<arg>)` or if you assign a value (even zero) to the new elements after increasing the length of the array.",
"link": "https://blog.soliditylang.org/2020/10/07/solidity-dynamic-array-cleanup-bug/",
"fixed": "0.7.3",
"severity": "medium"
},
{
"uid": "SOL-2020-9",
"name": "FreeFunctionRedefinition",
"summary": "The compiler does not flag an error when two or more free functionswith the same name and parameter types are defined in a source unit or when animported free function alias shadows another free function with a different name but identical parameter types.",
"description": "In contrast to functions defined inside contracts, freefunctions with identical names and parameter types did not create an error. Bothdefinition of free functions with identical name and parameter types and an importedfree function with an alias that shadows another function with a different name butidentical parameter types were permitted due to which a call to either the multiplydefined free function or the imported free function alias within a contract led to theexecution of that free function which was defined first within the source unit.Subsequently defined identical free function definitions were silently ignored and their code generation was skipped.",
"introduced": "0.7.1",
"fixed": "0.7.2",
"severity": "low"
},
{
"uid": "SOL-2020-8",
"name": "UsingForCalldata",
"summary": "Function calls to internal library functions with calldata parameters called via ``using for`` can result in invalid data being read.",
"description": "Function calls to internal library functions using the ``usingfor`` mechanism copied all calldata parameters to memory first and passed them on likethat, regardless of whether it was an internal or an external call. Due to that, thecalled function would receive a memory pointer that is interpreted as a calldatapointer. Since dynamically sized arrays are passed using two stack slots for calldata,but only one for memory, this can lead to stack corruption. An affected library callwill consider the JUMPDEST to which it is supposed to return as part of its arguments and will instead jump out to whatever was on the stack before the call.",
"introduced": "0.6.9",
"fixed": "0.6.10",
"severity": "very low"
},
{
"uid": "SOL-2020-7",
"name": "MissingEscapingInFormatting",
"summary": "String literals containing double backslash characters passeddirectly to external or encoding function calls can lead to a different string being used when ABIEncoderV2 is enabled.",
"description": "When ABIEncoderV2 is enabled, string literals passed directly toencoding functions or external function calls are stored as strings in theintermediate code. Characters outside the printable range are handled correctly, butbackslashes are not escaped in this procedure. This leads to double backslashes beingreduced to single backslashes and consequently re-interpreted as escapes potentially resulting in a different string being encoded.",
"introduced": "0.5.14",
"fixed": "0.6.8",
"severity": "very low",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2020-6",
"name": "ArraySliceDynamicallyEncodedBaseType",
"summary": "Accessing array slices of arrays with dynamically encoded base types (e.g. multi-dimensional arrays) can result in invalid data being read.",
"description": "For arrays with dynamically sized base types, index rangeaccesses that use a start expression that is non-zero will result in invalid arrayslices. Any index access to such array slices will result in data being read fromincorrect calldata offsets. Array slices are only supported for dynamic calldata types and all problematic type require ABIEncoderV2 to be enabled.",
"introduced": "0.6.0",
"fixed": "0.6.8",
"severity": "very low",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2020-5",
"name": "ImplicitConstructorCallvalueCheck",
"summary": "The creation code of a contract that does not define a constructorbut has a base that does define a constructor did not revert for calls with non-zerovalue.",
"description": "Starting from Solidity 0.4.5 the creation code of contractswithout explicit payable constructor is supposed to contain a callvalue check thatresults in contract creation reverting, if non-zero value is passed. However, thischeck was missing in case no explicit constructor was defined in a contract at all,but the contract has a base that does define a constructor. In these cases it ispossible to send value in a contract creation transaction or using inline assembly without revert, even though the creation code is supposed to be non-payable.",
"introduced": "0.4.5",
"fixed": "0.6.8",
"severity": "very low"
},
{
"uid": "SOL-2020-4",
"name": "TupleAssignmentMultiStackSlotComponents",
"summary": "Tuple assignments with components that occupy several stack slots, i.e. nested tuples, pointers to external functions or references to dynamically sized calldata arrays, can result in invalid values.",
"description": "Tuple assignments did not correctly account for tuple componentsthat occupy multiple stack slots in case the number of stack slots differs betweenleft-hand-side and right-hand-side. This can either happen in the presence of nestedtuples or if the right-hand-side contains external function pointers or references to dynamic calldata arrays, while the left-hand-side contains an omission.",
"introduced": "0.1.6",
"fixed": "0.6.6",
"severity": "very low"
},
{
"uid": "SOL-2020-3",
"name": "MemoryArrayCreationOverflow",
"summary": "The creation of very large memory arrays can result in overlapping memory regions and thus memory corruption.",
"description": "No runtime overflow checks were performed for the length ofmemory arrays during creation. In cases for which the memory size of an array in bytes, i.e. the array length times 32, is larger than 2^256-1, the memory allocation willoverflow, potentially resulting in overlapping memory areas. The length of the arrayis still stored correctly, so copying or iterating over such an array will result in out-of-gas.",
"link": "https://blog.soliditylang.org/2020/04/06/memory-creation-overflow-bug/",
"introduced": "0.2.0",
"fixed": "0.6.5",
"severity": "low"
},
{
"uid": "SOL-2020-1",
"name": "YulOptimizerRedundantAssignmentBreakContinue",
"summary": "The Yul optimizer can remove essential assignments to variablesdeclared inside for loops when Yul's continue or break statement is used. You areunlikely to be affected if you do not use inline assembly with for loops and continue and break statements.",
"description": "The Yul optimizer has a stage that removes assignments tovariables that are overwritten again or are not used in all following control-flowbranches. This logic incorrectly removes such assignments to variables declared insidea for loop if they can be removed in a control-flow branch that ends with ``break`` or``continue`` even though they cannot be removed in other control-flow branches. Variables declared outside of the respective for loop are not affected.",
"introduced": "0.6.0",
"fixed": "0.6.1",
"severity": "medium",
"conditions": {
"yulOptimizer": true
}
},
{
"uid": "SOL-2020-2",
"name": "privateCanBeOverridden",
"summary": "Private methods can be overridden by inheriting contracts.",
"description": "While private methods of base contracts are not visible andcannot be called directly from the derived contract, it is still possible to declare afunction of the same name and type and thus change the behaviour of the base contract's function.",
"introduced": "0.3.0",
"fixed": "0.5.17",
"severity": "low"
},
{
"uid": "SOL-2020-1",
"name": "YulOptimizerRedundantAssignmentBreakContinue0.5",
"summary": "The Yul optimizer can remove essential assignments to variablesdeclared inside for loops when Yul's continue or break statement is used. You areunlikely to be affected if you do not use inline assembly with for loops and continue and break statements.",
"description": "The Yul optimizer has a stage that removes assignments tovariables that are overwritten again or are not used in all following control-flowbranches. This logic incorrectly removes such assignments to variables declared insidea for loop if they can be removed in a control-flow branch that ends with ``break`` or``continue`` even though they cannot be removed in other control-flow branches. Variables declared outside of the respective for loop are not affected.",
"introduced": "0.5.8",
"fixed": "0.5.16",
"severity": "low",
"conditions": {
"yulOptimizer": true
}
},
{
"uid": "SOL-2019-10",
"name": "ABIEncoderV2LoopYulOptimizer",
"summary": "If both the experimental ABIEncoderV2 and the experimental Yuloptimizer are activated, one component of the Yul optimizer may reuse data in memory that has been changed in the meantime.",
"description": "The Yul optimizer incorrectly replaces ``mload`` and ``sload``calls with values that have been previously written to the load location (andpotentially changed in the meantime) if all of the following conditions are met: (1)there is a matching ``mstore`` or ``sstore`` call before; (2) the contents of memoryor storage is only changed in a function that is called (directly or indirectly) inbetween the first store and the load call; (3) called function contains a for loopwhere the same memory location is changed in the condition or the post or body block.When used in Solidity mode, this can only happen if the experimental ABIEncoderV2 isactivated and the experimental Yul optimizer has been activated manually in addition to the regular optimizer in the compiler settings.",
"introduced": "0.5.14",
"fixed": "0.5.15",
"severity": "low",
"conditions": {
"ABIEncoderV2": true,
"optimizer": true,
"yulOptimizer": true
}
},
{
"uid": "SOL-2019-9",
"name":
```

``` "ABIEncoderV2CalldataStructsWithStaticallySizedAndDynamicallyEncodedMembers",
"summary": "Reading from calldata structs that contain dynamically encoded, but statically-sized members can result in incorrect values.",
"description": "When a calldata struct contains a dynamically encoded, butstatically-sized member, the offsets for all subsequent struct members are calculatedincorrectly. All reads from such members will result in invalid values. Only calldatastructs are affected, i.e. this occurs in external functions with such structs asargument. Using affected structs in storage or memory or as arguments to public functions on the other hand works correctly.",
"introduced": "0.5.6",
"fixed": "0.5.11",
"severity": "low",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2019-8",
"name": "SignedArrayStorageCopy",
"summary": "Assigning an array of signed integers to a storage array of different type can lead to data corruption in that array.",
"description": "In two's complement, negative integers have their higher orderbits set. In order to fit into a shared storage slot, these have to be set to zero.When a conversion is done at the same time, the bits to set to zero were incorrectlydetermined from the source and not the target type. This means that such copy operations can lead to incorrect values being stored.",
"link": "https://blog.soliditylang.org/2019/06/25/solidity-storage-array-bugs/",
"introduced": "0.4.7",
"fixed": "0.5.10",
"severity": "low/medium"
},
{
"uid": "SOL-2019-7",
"name": "ABIEncoderV2StorageArrayWithMultiSlotElement",
"summary": "Storage arrays containing structs or other statically-sized arraysare not read properly when directly encoded in external function calls or in abi.encode*.",
"description": "When storage arrays whose elements occupy more than a singlestorage slot are directly encoded in external function calls or using abi.encode*,their elements are read in an overlapping manner, i.e. the element pointer is notproperly advanced between reads. This is not a problem when the storage data is firstcopied to a memory variable or if the storage array only contains value types or dynamically-sized arrays.",
"link": "https://blog.soliditylang.org/2019/06/25/solidity-storage-array-bugs/",
"introduced": "0.4.16",
"fixed": "0.5.10",
"severity": "low",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2019-6",
"name": "DynamicConstructorArgumentsClippedABIV2",
"summary": "A contract's constructor that takes structs or arrays that contain dynamically-sized arrays reverts or decodes to invalid data.",
"description": "During construction of a contract, constructor parameters arecopied from the code section to memory for decoding. The amount of bytes to copy wascalculated incorrectly in case all parameters are statically-sized but containdynamically-sized arrays as struct members or inner arrays. Such types are only available if ABIEncoderV2 is activated.",
"introduced": "0.4.16",
"fixed": "0.5.9",
"severity": "very low",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2019-5",
"name": "UninitializedFunctionPointerInConstructor",
"summary": "Calling uninitialized internal function pointers created in the constructor does not always revert and can cause unexpected behaviour.",
"description": "Uninitialized internal function pointers point to a specialpiece of code that causes a revert when called. Jump target positions are differentduring construction and after deployment, but the code for setting this special jump target only considered the situation after deployment.",
"introduced": "0.5.0",
"fixed": "0.5.8",
"severity": "very low"
},
{
"uid": "SOL-2019-5",
"name": "UninitializedFunctionPointerInConstructor_0.4.x",
"summary": "Calling uninitialized internal function pointers created in the constructor does not always revert and can cause unexpected behaviour.",
"description": "Uninitialized internal function pointers point to a specialpiece of code that causes a revert when called. Jump target positions are differentduring construction and after deployment, but the code for setting this special jump target only considered the situation after deployment.",
"introduced": "0.4.5",
"fixed": "0.4.26",
"severity": "very low"
},
{
"uid": "SOL-2019-4",
"name": "IncorrectEventSignatureInLibraries",
"summary": "Contract types used in events in libraries cause an incorrect event signature hash",
"description": "Instead of using the type `address` in the hashed signature, the actual contract name was used, leading to a wrong hash in the logs.",
"introduced": "0.5.0",
"fixed": "0.5.8",
"severity": "very low"
},
{
"uid": "SOL-2019-4",
"name": "IncorrectEventSignatureInLibraries_0.4.x",
"summary": "Contract types used in events in libraries cause an incorrect event signature hash",
"description": "Instead of using the type `address` in the hashed signature, the actual contract name was used, leading to a wrong hash in the logs.",
"introduced": "0.3.0",
"fixed": "0.4.26",
"severity": "very low"
},
{
"uid": "SOL-2019-3",
"name": "ABIEncoderV2PackedStorage",
"summary": "Storage structs and arrays with types shorter than 32 bytes cancause data corruption if encoded directly from storage using the experimentalABIEncoderV2.",
"description": "Elements of structs and arrays that are shorter than 32 bytesare not properly decoded from storage when encoded directly (i.e. not via a memorytype) using ABIEncoderV2. This can cause corruption in the values themselves but can also overwrite other parts of the encoded data.",
"link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and- abiencoderv2-bug/",
"introduced": "0.5.0",
"fixed": "0.5.7",
"severity": "low",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2019-3",
"name": "ABIEncoderV2PackedStorage_0.4.x",
"summary": "Storage structs and arrays with types shorter than 32 bytes cancause data corruption if encoded directly from storage using the experimentalABIEncoderV2.",
"description": "Elements of structs and arrays that are shorter than 32 bytesare not properly decoded from storage when encoded directly (i.e. not via a memorytype) using ABIEncoderV2. This can cause corruption in the values themselves but can also overwrite other parts of the encoded data.",
"link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and- abiencoderv2-bug/",
"introduced": "0.4.19",
"fixed": "0.4.26",
"severity": "low",
"conditions": {
"ABIEncoderV2": true
}
},
{
"uid": "SOL-2019-2",
"name": "IncorrectByteInstructionOptimization",
"summary": "The optimizer incorrectly handles byte opcodes whose second argumentis 31 or a constant expression that evaluates to 31. This can result in unexpectedvalues.",
"description": "The optimizer incorrectly handles byte opcodes that use theconstant 31 as second argument. This can happen when performing index access onbytesNN types with a compile-time constant value (not index) of 31 or when using the byte opcode in inline assembly.",
"link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and- abiencoderv2-bug/",
"introduced": "0.5.5",
"fixed": "0.5.7",
"severity": "very low",
"conditions": {
"optimizer": true
}
},
{
"uid": "SOL-2019-1",
"name": "DoubleShiftSizeOverflow",
"summary": "Double bitwise shifts by large constants whose sum overflows 256 bits can result in unexpected values.",
"description": "Nested logical shift operations whose total shift size is 2**256or more are incorrectly optimized. This only applies to shifts by numbers of bits that are compile-time constant expressions.",
"link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and- abiencoderv2-bug/",
"introduced": "0.5.5",
"fixed": "0.5.6",
"severity": "low",
"conditions": {
"optimizer": true,
"evmVersion": ">=constantinople"
}
},
{
"uid": "SOL-2018-4",
"name": "ExpExponentCleanup",
"summary": "Using the ** operator with an exponent of type shorter than 256 bits can result in unexpected values.",
"description": "Higher order bits in the exponent are not properly cleanedbefore the EXP opcode is applied if the type of the exponent expression is smallerthan 256 bits and not smaller than the type of the base. In that case, the resultmight be larger than expected if the exponent is assumed to lie within the value range of the type. Literal numbers as exponents are unaffected as are exponents or bases of
```

``` type uint256.",
"link": "https://blog.soliditylang.org/2018/09/13/solidity-bugfix-release/",
"fixed": "0.4.25",
"severity": "medium/high",
"check": {"regex-source": "[^/]\\*\\* *[^/0-9 ]"}
},
{
"uid": "SOL-2018-3",
"name": "EventStructWrongData",
"summary": "Using structs in events logged wrong data.",
"description": "If a struct is used in an event, the address of the struct is logged instead of the actual data.",
"link": "https://blog.soliditylang.org/2018/09/13/solidity-bugfix-release/",
"introduced": "0.4.17",
"fixed": "0.4.25",
"severity": "very low",
"check": {"ast-compact-json-path": "$..[?(@.nodeType === 'EventDefinition')]..[?(@.nodeType === 'UserDefinedTypeName' && @.typeDescriptions.typeString.startsWith( 'struct'))]"}
},
{
"uid": "SOL-2018-2",
"name": "NestedArrayFunctionCallDecoder",
"summary": "Calling functions that return multi-dimensional fixed-size arrays can result in memory corruption.",
"description": "If Solidity code calls a function that returns a multi-dimensional fixed-size array, array elements are incorrectly interpreted as memorypointers and thus can cause memory corruption if the return values are accessed.Calling functions with multi-dimensional fixed-size arrays is unaffected as isreturning fixed-size arrays from function calls. The regular expression only checks ifsuch functions are present, not if they are called, which is required for the contract to be affected.",
"link": "https://blog.soliditylang.org/2018/09/13/solidity-bugfix-release/",
"introduced": "0.1.4",
"fixed": "0.4.22",
"severity": "medium",
"check": {"regex-source": "returns[^;{]*\\[\\s*[^\\] \\t\\r\\n\\v\\f][^\\]]*\\]\\ s*\\[\\s*[^\\] \\t\\r\\n\\v\\f][^\\]]*\\][^{;]*[;{]"}
},
{
"uid": "SOL-2018-1",
"name": "OneOfTwoConstructorsSkipped",
"summary": "If a contract has both a new-style constructor (using theconstructor keyword) and an old-style constructor (a function with the same name as the contract) at the same time, one of them will be ignored.",
"description": "If a contract has both a new-style constructor (using theconstructor keyword) and an old-style constructor (a function with the same name asthe contract) at the same time, one of them will be ignored. There will be a compilerwarning about the old-style constructor, so contracts only using new-style constructors are fine.",
"introduced": "0.4.22",
"fixed": "0.4.23",
"severity": "very low"
},
{
"uid": "SOL-2017-5",
"name": "ZeroFunctionSelector",
"summary": "It is possible to craft the name of a function such that it is executed instead of the fallback function in very specific circumstances.",
"description": "If a function has a selector consisting only of zeros, ispayable and part of a contract that does not have a fallback function and at most fiveexternal functions in total, this function is called instead of the fallback function if Ether is sent to the contract without data.",
"fixed": "0.4.18",
"severity": "very low"
},
{
"uid": "SOL-2017-4",
"name": "DelegateCallReturnValue",
"summary": "The low-level .delegatecall() does not return the execution outcome, but converts the value returned by the functioned called to a boolean instead.",
"description": "The return value of the low-level .delegatecall() function istaken from a position in memory, where the call data or the return data resides. Thisvalue is interpreted as a boolean and put onto the stack. This means if the calledfunction returns at least 32 zero bytes, .delegatecall() returns false even if the call was successful.",
"introduced": "0.3.0",
"fixed": "0.4.15",
"severity": "low"
},
{
"uid": "SOL-2017-3",
"name": "ECRecoverMalformedInput",
"summary": "The ecrecover() builtin can return garbage for malformed input.",
"description": "The ecrecover precompile does not properly signal failure formalformed input (especially in the 'v' argument) and thus the Solidity function can return data that was previously present in the return area in memory.",
"fixed": "0.4.14",
"severity": "medium"
},
{
"uid": "SOL-2017-2",
"name": "SkipEmptyStringLiteral",
"summary": "If \"\" is used in a function call, the following function arguments will not be correctly passed to the function.",
"description": "If the empty string literal \"\" is used as an argument in afunction call, it is skipped by the encoder. This has the effect that the encoding ofall arguments following this is shifted left by 32 bytes and thus the function call data is corrupted.",
"fixed": "0.4.12",
"severity": "low"
},
{
"uid": "SOL-2017-1",
"name": "ConstantOptimizerSubtraction",
"summary": "In some situations, the optimizer replaces certain numbers in the code with routines that compute different numbers.",
"description": "The optimizer tries to represent any number in the bytecode byroutines that compute them with less gas. For some special numbers, an incorrectroutine is generated. This could allow an attacker to e.g. trick victims about aspecific amount of ether, or function calls to call different functions (or none atall).",
"link": "https://blog.soliditylang.org/2017/05/03/solidity-optimizer-bug/",
"fixed": "0.4.11",
"severity": "low",
"conditions": {
"optimizer": true
}
},
{
"uid": "SOL-2016-11",
"name": "IdentityPrecompileReturnIgnored",
"summary": "Failure of the identity precompile was ignored.",
"description": "Calls to the identity contract, which is used for copying memory, ignored its return value. On the public chain, calls to the identity precompile can be made in a way that they never fail, but this might be different on private chains.",
"severity": "low",
"fixed": "0.4.7"
},
{
"uid": "SOL-2016-10",
"name": "OptimizerStateKnowledgeNotResetForJumpdest",
"summary": "The optimizer did not properly reset its internal state at jump destinations, which could lead to data corruption.",
"description": "The optimizer performs symbolic execution at certain stages. Atjump destinations, multiple code paths join and thus it has to compute a common statefrom the incoming edges. Computing this common state was simplified to just use theempty state, but this implementation was not done properly. This bug can cause data corruption.",
"severity": "medium",
"introduced": "0.4.5",
"fixed": "0.4.6",
"conditions": {
"optimizer": true
}
},
{
"uid": "SOL-2016-9",
"name": "HighOrderByteCleanStorage",
"summary": "For short types, the high order bytes were not cleaned properly and could overwrite existing data.",
"description": "Types shorter than 32 bytes are packed together into the same 32byte storage slot, but storage writes always write 32 bytes. For some types, thehigher order bytes were not cleaned properly, which made it sometimes possible to overwrite a variable in storage when writing to another one.",
"link": "https://blog.soliditylang.org/2016/11/01/security-alert-solidity-
```

``` variables-can-overwritten-storage/",
"severity": "high",
"introduced": "0.1.6",
"fixed": "0.4.4"
},
{
"uid": "SOL-2016-8",
"name": "OptimizerStaleKnowledgeAboutSHA3",
"summary": "The optimizer did not properly reset its knowledge about SHA3operations resulting in some hashes (also used for storage variable positions) not being calculated correctly.",
"description": "The optimizer performs symbolic execution in order to save re-evaluating expressions whose value is already known. This knowledge was not properlyreset across control flow paths and thus the optimizer sometimes thought that theresult of a SHA3 operation is already present on the stack. This could result in data corruption by accessing the wrong storage slot.",
"severity": "medium",
"fixed": "0.4.3",
"conditions": {
"optimizer": true
}
},
{
"uid": "SOL-2016-7",
"name": "LibrariesNotCallableFromPayableFunctions",
"summary": "Library functions threw an exception when called from a call that received Ether.",
"description": "Library functions are protected against sending them Etherthrough a call. Since the DELEGATECALL opcode forwards the information about how muchEther was sent with a call, the library function incorrectly assumed that Ether was sent to the library and threw an exception.",
"severity": "low",
"introduced": "0.4.0",
"fixed": "0.4.2"
},
{
"uid": "SOL-2016-6",
"name": "SendFailsForZeroEther",
"summary": "The send function did not provide enough gas to the recipient if no Ether was sent with it.",
"description": "The recipient of an Ether transfer automatically receives acertain amount of gas from the EVM to handle the transfer. In the case of a zero- transfer, this gas is not provided which causes the recipient to throw an exception.",
"severity": "low",
"fixed": "0.4.0"
},
{
"uid": "SOL-2016-5",
"name": "DynamicAllocationInfiniteLoop",
"summary": "Dynamic allocation of an empty memory array caused an infinite loop and thus an exception.",
"description": "Memory arrays can be created provided a length. If this length
 is zero, code was generated that did not terminate and thus consumed all gas.",
"severity": "low",
"fixed": "0.3.6"
},
{
"uid": "SOL-2016-4",
"name": "OptimizerClearStateOnCodePathJoin",
"summary": "The optimizer did not properly reset its internal state at jump destinations, which could lead to data corruption.",
"description": "The optimizer performs symbolic execution at certain stages. Atjump destinations, multiple code paths join and thus it has to compute a common statefrom the incoming edges. Computing this common state was not done correctly. This bug can cause data corruption, but it is probably quite hard to use for targeted attacks.",
"severity": "low",
"fixed": "0.3.6",
"conditions": {
"optimizer": true
}
},
{
"uid": "SOL-2016-3",
"name": "CleanBytesHigherOrderBits",
"summary": "The higher order bits of short bytesNN types were not cleaned beforecomparison.",
"description": "Two variables of type bytesNN were considered different if theirhigher order bits, which are not part of the actual value, were different. An attackermight use this to reach seemingly unreachable code paths by providing incorrectly formatted input data.",
"severity": "medium/high",
"fixed": "0.3.3"
},
{
"uid": "SOL-2016-2",
"name": "ArrayAccessCleanHigherOrderBits",
"summary": "Access to array elements for arrays of types with less than 32 bytesdid not correctly clean the higher order bits, causing corruption in other arrayelements.",
"description": "Multiple elements of an array of values that are shorter than 17bytes are packed into the same storage slot. Writing to a single element of such anarray did not properly clean the higher order bytes and thus could lead to data corruption.",
"severity": "medium/high",
"fixed": "0.3.1"
},
{
"uid": "SOL-2016-1",
"name": "AncientCompiler",
"summary": "This compiler version is ancient and might contain several undocumented or undiscovered bugs.",
"description": "The list of bugs is only kept for compiler versions starting from 0.3.0, so older versions might contain undocumented bugs.",
"severity": "high",
```

"fixed": "0.3.0"

}

]
